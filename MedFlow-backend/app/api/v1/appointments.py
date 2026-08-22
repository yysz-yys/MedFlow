from datetime import date as date_type, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db; from app.core.deps import require_role, get_current_user
from app.models.appointment import Appointment; from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentOut
from app.services.appointment_service import create_appointment, cancel_appointment, complete_appointment, restore_appointment, uncomplete_appointment

router = APIRouter(prefix="/appointments", tags=["挂号"])

# ===== 统计聚合端点（必须在 /{apt_id} 动态路由之前） =====

@router.get("/stats/daily")
async def stats_daily(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """返回最近 N 天每天的挂号数量"""
    from sqlalchemy import func
    end = date_type.today()
    start = end - timedelta(days=days - 1)
    results = await db.execute(
        select(
            func.date(Appointment.appointment_time).label("d"),
            func.count(Appointment.id).label("c"),
        )
        .where(
            Appointment.appointment_time >= start,
            Appointment.appointment_time < end + timedelta(days=1),
        )
        .group_by(func.date(Appointment.appointment_time))
        .order_by("d")
    )
    rows = results.all()
    row_map = {str(r.d): r.c for r in rows}
    data = []
    current = start
    while current <= end:
        key = current.isoformat()
        data.append({"date": key, "count": row_map.get(key, 0)})
        current += timedelta(days=1)
    return data


@router.get("/stats/by-dept")
async def stats_by_dept(
    date: date_type = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """返回指定日期各科室挂号数量，降序排列"""
    from sqlalchemy import func
    target = date or date_type.today()
    start = datetime.combine(target, datetime.min.time())
    end = start + timedelta(days=1)
    results = await db.execute(
        select(
            Department.name.label("department_name"),
            func.count(Appointment.id).label("count"),
        )
        .join(Department, Appointment.department_id == Department.id)
        .where(
            Appointment.appointment_time >= start,
            Appointment.appointment_time < end,
        )
        .group_by(Department.name)
        .order_by(func.count(Appointment.id).desc())
    )
    rows = results.all()
    return [{"department_name": r.department_name, "count": r.count} for r in rows]


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    status: int = None,
    date: date_type = None,
    start_date: date_type = None,
    end_date: date_type = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)):
    query = select(Appointment).options(
        joinedload(Appointment.patient).joinedload(Patient.user),
        joinedload(Appointment.doctor).joinedload(Doctor.user),
        joinedload(Appointment.department),
        joinedload(Appointment.schedule)
    )
    if current_user.role == 0:  # 管理员看全部
        pass
    elif current_user.role == 1:  # 医生看自己的
        result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doctor = result.scalar_one_or_none()
        if doctor: query = query.where(Appointment.doctor_id == doctor.id)
    else:  # 病人看自己的
        result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
        patient = result.scalar_one_or_none()
        if patient: query = query.where(Appointment.patient_id == patient.id)
    if status is not None: query = query.where(Appointment.status == status)

    # NEW: date filters
    if date:
        query = query.where(
            Appointment.appointment_time >= datetime.combine(date, datetime.min.time()),
            Appointment.appointment_time < datetime.combine(date, datetime.max.time()),
        )
    else:
        if start_date:
            query = query.where(Appointment.appointment_time >= start_date)
        if end_date:
            query = query.where(Appointment.appointment_time < end_date + timedelta(days=1))

    query = query.order_by(Appointment.appointment_time.desc())
    apts = (await db.execute(query)).scalars().all()

    # 批量查询各排班的已约人数
    booked_map: dict = {}
    schedule_ids = {a.schedule_id for a in apts if a.schedule_id}
    if schedule_ids:
        from sqlalchemy import func
        count_rows = (await db.execute(
            select(Appointment.schedule_id, func.count(Appointment.id))
            .where(Appointment.schedule_id.in_(schedule_ids), Appointment.status == 1)
            .group_by(Appointment.schedule_id)
        )).all()
        booked_map = {row[0]: row[1] for row in count_rows}

    return [AppointmentOut(id=a.id,patient_id=a.patient_id,doctor_id=a.doctor_id,
            department_id=a.department_id,patient_name=a.patient.user.name,
            doctor_name=a.doctor.user.name,department_name=a.department.name if a.department else None,
            appointment_time=a.appointment_time.isoformat() if a.appointment_time else None,
            status=a.status,
            schedule_start_time=a.schedule.start_time.strftime('%H:%M') if a.schedule else None,
            schedule_end_time=a.schedule.end_time.strftime('%H:%M') if a.schedule else None,
            schedule_max_patients=a.schedule.max_patients if a.schedule else None,
            schedule_booked_count=booked_map.get(a.schedule_id) if a.schedule_id else None,
            created_at=a.created_at.isoformat() if a.created_at else None) for a in apts]

@router.post("", response_model=AppointmentOut)
async def create(req: AppointmentCreate, current_user=Depends(require_role([2])),
                 db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(
        Patient.user_id == current_user.id, Patient.deleted_at.is_(None)))
    patient = result.scalar_one_or_none()
    if patient is None: raise HTTPException(status_code=400, detail="请先完善病人档案")
    apt = await create_appointment(db, patient.id, req.doctor_id, req.schedule_id)
    return AppointmentOut(id=apt.id,patient_id=apt.patient_id,doctor_id=apt.doctor_id,
            department_id=apt.department_id,status=apt.status)

@router.put("/{apt_id}")
async def update(apt_id: int, req: AppointmentUpdate, current_user=Depends(require_role([2])),
                 db: AsyncSession = Depends(get_db)):
    apt = (await db.execute(select(Appointment).where(Appointment.id == apt_id))).scalar_one_or_none()
    if apt is None: raise HTTPException(status_code=404)
    if req.doctor_id is not None: apt.doctor_id = req.doctor_id
    return {"message": "更新成功"}

@router.post("/{apt_id}/cancel")
async def cancel(apt_id: int, current_user=Depends(require_role([2])),
                 db: AsyncSession = Depends(get_db)):
    await cancel_appointment(db, apt_id, current_user.id)
    return {"message": "已取消"}

@router.post("/{apt_id}/restore")
async def restore(apt_id: int, current_user=Depends(require_role([2])),
                  db: AsyncSession = Depends(get_db)):
    await restore_appointment(db, apt_id, current_user.id)
    return {"message": "已恢复"}

@router.post("/{apt_id}/complete")
async def complete(apt_id: int, current_user=Depends(require_role([1])),
                   db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if doctor is None: raise HTTPException(status_code=400, detail="医生档案不存在")
    await complete_appointment(db, apt_id, doctor.id)
    return {"message": "已标记就诊完成"}

@router.post("/{apt_id}/uncomplete")
async def uncomplete(apt_id: int, current_user=Depends(require_role([1])),
                     db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if doctor is None: raise HTTPException(status_code=400, detail="医生档案不存在")
    await uncomplete_appointment(db, apt_id, doctor.id)
    return {"message": "已撤销就诊完成"}
