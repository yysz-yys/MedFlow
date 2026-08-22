from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.patient import Patient
from app.models.user import User
from datetime import datetime, timezone, timedelta

async def create_appointment(db: AsyncSession, patient_id: int, doctor_id: int, schedule_id: int):
    doctor = (await db.execute(
        select(Doctor).options(joinedload(Doctor.user)).where(Doctor.id == doctor_id, Doctor.deleted_at.is_(None))
    )).scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=404, detail="医生不存在")

    schedule = (await db.execute(
        select(DoctorSchedule).where(DoctorSchedule.id == schedule_id, DoctorSchedule.status == 1)
    )).scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=400, detail="该时段不可预约")

    slot_start = datetime.combine(schedule.work_date, schedule.start_time)
    slot_end = datetime.combine(schedule.work_date, schedule.end_time)

    # 0. 可预约时间 = 开始后30分钟 ~ 结束前30分钟，时长不足30分钟则不可约
    slot_duration = (slot_end - slot_start).total_seconds() / 60
    if slot_duration <= 30:
        raise HTTPException(status_code=400, detail="该时段时长不足，不可预约")
    bookable_start = slot_start + timedelta(minutes=30)

    # 1. 防止同一病人重复预约同一时段（已有有效挂号）
    dup_active = (await db.execute(
        select(func.count()).select_from(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.schedule_id == schedule_id,
            Appointment.status == 1,
        )
    )).scalar()
    if dup_active > 0:
        raise HTTPException(status_code=400, detail="您已预约过该时段，请勿重复预约")

    # 2. 检查该时段已约人数
    booked = (await db.execute(
        select(func.count()).select_from(Appointment).where(
            Appointment.schedule_id == schedule_id,
            Appointment.status == 1,
        )
    )).scalar()

    # 3. 检查是否有该排班已取消的挂号，有则直接恢复
    canceled = (await db.execute(
        select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.schedule_id == schedule_id,
            Appointment.status == 0,
        ).limit(1)
    )).scalar_one_or_none()
    if canceled:
        if booked >= schedule.max_patients:
            raise HTTPException(status_code=400, detail="该时段已约满")
        canceled.status = 1
        canceled.appointment_time = bookable_start
        await db.flush()
        from app.services.notification_service import create_notification
        await create_notification(db, doctor.user_id, "挂号提醒",
            f"重新预约：{schedule.work_date} {schedule.start_time}", "APPOINTMENT", "appointment", canceled.id)
        return canceled

    # 4. 容量检查 → 新建
    if booked >= schedule.max_patients:
        raise HTTPException(status_code=400, detail="该时段已约满")

    apt = Appointment(
        patient_id=patient_id, doctor_id=doctor_id, department_id=doctor.department_id,
        schedule_id=schedule_id,
        appointment_time=bookable_start,
    )
    db.add(apt)
    await db.flush()

    from app.services.notification_service import create_notification
    await create_notification(db, doctor.user_id, "挂号提醒",
        f"新预约：{schedule.work_date} {schedule.start_time}", "APPOINTMENT", "appointment", apt.id)
    return apt

async def cancel_appointment(db: AsyncSession, apt_id: int, patient_user_id: int):
    apt = (await db.execute(
        select(Appointment).options(joinedload(Appointment.patient).joinedload(Patient.user),
                                     joinedload(Appointment.doctor).joinedload(Doctor.user))
        .where(Appointment.id == apt_id)
    )).scalar_one_or_none()
    if apt is None: raise HTTPException(status_code=404, detail="挂号不存在")
    if apt.patient.user_id != patient_user_id:
        raise HTTPException(status_code=403, detail="只能取消自己的挂号")
    if apt.status != 1:
        raise HTTPException(status_code=400, detail="仅待就诊的挂号可取消")
    apt.status = 0
    from app.services.notification_service import create_notification
    await create_notification(db, apt.doctor.user_id, "挂号取消",
        f"挂号已取消：{apt.appointment_time}", "APPOINTMENT", "appointment", apt.id)
    return apt

async def restore_appointment(db: AsyncSession, apt_id: int, patient_user_id: int):
    apt = (await db.execute(
        select(Appointment).options(joinedload(Appointment.patient).joinedload(Patient.user),
                                     joinedload(Appointment.doctor).joinedload(Doctor.user))
        .where(Appointment.id == apt_id)
    )).scalar_one_or_none()
    if apt is None: raise HTTPException(status_code=404, detail="挂号不存在")
    if apt.patient.user_id != patient_user_id:
        raise HTTPException(status_code=403, detail="只能恢复自己的挂号")
    if apt.status != 0:
        raise HTTPException(status_code=400, detail="仅已取消的挂号可恢复")
    # 检查时段是否还有名额
    if apt.schedule_id:
        booked = (await db.execute(
            select(func.count()).select_from(Appointment).where(
                Appointment.schedule_id == apt.schedule_id,
                Appointment.status == 1,
            )
        )).scalar()
        schedule = (await db.execute(
            select(DoctorSchedule).where(DoctorSchedule.id == apt.schedule_id)
        )).scalar_one_or_none()
        if schedule and booked >= schedule.max_patients:
            raise HTTPException(status_code=400, detail="该时段已约满，无法恢复")
    apt.status = 1
    from app.services.notification_service import create_notification
    await create_notification(db, apt.doctor.user_id, "挂号恢复",
        f"挂号已恢复：{apt.appointment_time}", "APPOINTMENT", "appointment", apt.id)
    return apt

async def complete_appointment(db: AsyncSession, apt_id: int, doctor_id: int):
    apt = (await db.execute(
        select(Appointment).where(Appointment.id == apt_id)
    )).scalar_one_or_none()
    if apt is None: raise HTTPException(status_code=404, detail="挂号不存在")
    if apt.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="只能操作自己的挂号")
    if apt.status != 1:
        raise HTTPException(status_code=400, detail="仅待就诊的挂号可标记完成")
    apt.status = 2
    return apt

async def uncomplete_appointment(db: AsyncSession, apt_id: int, doctor_id: int):
    apt = (await db.execute(
        select(Appointment).where(Appointment.id == apt_id)
    )).scalar_one_or_none()
    if apt is None: raise HTTPException(status_code=404, detail="挂号不存在")
    if apt.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="只能操作自己的挂号")
    if apt.status != 2:
        raise HTTPException(status_code=400, detail="仅已完成的挂号可撤销")
    apt.status = 1
    return apt
