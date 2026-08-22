from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete as sqla_delete, update as sqla_update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.models.doctor_schedule import DoctorSchedule
from app.models.doctor import Doctor
from app.schemas.doctor_schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleOut,
    TemplateSaveRequest, ReapplyRequest,
)
from datetime import date, time, timedelta, datetime

router = APIRouter(prefix="/doctor-schedules", tags=["排班"])

# 兜底模板: 从 system_config 读取 default_doctor_schedule，失败则用硬编码
FALLBACK_DEFAULT = "08:00,11:30,13:30,17:00,19:00,21:30"

def _get_template_fallback() -> list[dict]:
    """动态生成兜底模板: 周一到周五，上午/下午/晚上"""
    from app.core.sysconfig import get as sysconfig_get
    raw = sysconfig_get("default_doctor_schedule", FALLBACK_DEFAULT)
    try:
        parts = raw.split(",")
        if len(parts) != 6:
            parts = FALLBACK_DEFAULT.split(",")
        morning_start, morning_end, afternoon_start, afternoon_end, evening_start, evening_end = parts
    except Exception:
        morning_start, morning_end, afternoon_start, afternoon_end, evening_start, evening_end = FALLBACK_DEFAULT.split(",")

    def _s(t):
        return t.strip() + ":00" if len(t.strip()) == 5 else t.strip()

    slots = [
        (morning_start, morning_end),
        (afternoon_start, afternoon_end),
        (evening_start, evening_end),
    ]
    result = []
    for wd in range(1, 6):  # 周一~周五
        for s, e in slots:
            result.append({"weekday": wd, "start": _s(s), "end": _s(e), "max_patients": 20})
    return result

def _read_weekday(d: date) -> int:
    """从模板日期中读取 weekday: 0=周日~6=周六 (存为 date(2000,1,2+weekday))"""
    return (d.weekday() + 1) % 7

def _make_template_date(weekday: int) -> date:
    """将 weekday 编码为日期: date(2000,1,2+weekday) 其中 0=周日"""
    return date(2000, 1, 2 + weekday)

async def get_template_slots(db: AsyncSession, doctor_id: int) -> list[dict]:
    """获取医生的模板时段。优先级: 专属模板(-N) → 默认模板(0) → 硬编码"""
    # ① 查专属模板
    template_id = -abs(doctor_id)
    result = await db.execute(
        select(DoctorSchedule).where(DoctorSchedule.doctor_id == template_id)
    )
    rows = result.scalars().all()
    if rows:
        return [{"weekday": _read_weekday(r.work_date),
                 "start": str(r.start_time), "end": str(r.end_time),
                 "max_patients": r.max_patients} for r in rows]
    # ② 查默认模板
    result = await db.execute(
        select(DoctorSchedule).where(DoctorSchedule.doctor_id == 0)
    )
    rows = result.scalars().all()
    if rows:
        return [{"weekday": _read_weekday(r.work_date),
                 "start": str(r.start_time), "end": str(r.end_time),
                 "max_patients": r.max_patients} for r in rows]
    # ③ 硬编码兜底
    return _get_template_fallback()

async def auto_generate_schedules(
    db: AsyncSession, department_id: int,
    work_date_from: date, work_date_to: date,
) -> int:
    """按模板自动生成排班，跳过已有实际排班的医生，返回生成记录数"""
    result = await db.execute(
        select(Doctor.id).where(
            Doctor.department_id == department_id,
            Doctor.deleted_at.is_(None),
        )
    )
    doctor_ids = [r[0] for r in result.all()]

    total = 0
    for did in doctor_ids:
        # 检查该医生该周是否已有实际排班
        existing = await db.execute(
            select(DoctorSchedule.id).where(
                DoctorSchedule.doctor_id == did,
                DoctorSchedule.work_date >= work_date_from,
                DoctorSchedule.work_date <= work_date_to,
            ).limit(1)
        )
        if existing.scalars().first():
            continue

        template = await get_template_slots(db, did)
        current = work_date_from
        while current <= work_date_to:
            py_wd = current.weekday()  # 0=Mon
            our_wd = (py_wd + 1) % 7   # 0=Sun
            for slot in template:
                if slot["weekday"] == our_wd:
                    db.add(DoctorSchedule(
                        doctor_id=did,
                        work_date=current,
                        start_time=time.fromisoformat(slot["start"]),
                        end_time=time.fromisoformat(slot["end"]),
                        max_patients=slot["max_patients"],
                        status=1,
                    ))
                    total += 1
            current += timedelta(days=1)

    if total > 0:
        await db.flush()
    return total

# ========== 排班查询（改造：自动生成） ==========

@router.get("", response_model=list[ScheduleOut])
async def list_schedules(
    doctor_id: int = None,
    department_id: int = None,
    work_date_from: date = None,
    work_date_to: date = None,
    date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # date 便捷参数 → work_date_from = work_date_to = date
    if date:
        work_date_from = date
        work_date_to = date
    # 医生自动只看自己的排班
    if current_user.role == 1 and not doctor_id:
        doc = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
        if doc: doctor_id = doc.id
    # 自动生成: 如果按科室+日期查且该周无排班，自动生成
    if department_id and work_date_from and work_date_to:
        doctor_subq = select(Doctor.id).where(
            Doctor.department_id == department_id,
            Doctor.deleted_at.is_(None),
        )
        existing = await db.execute(
            select(DoctorSchedule.id).where(
                DoctorSchedule.doctor_id.in_(doctor_subq),
                DoctorSchedule.work_date >= work_date_from,
                DoctorSchedule.work_date <= work_date_to,
                DoctorSchedule.doctor_id > 0,
            ).limit(1)
        )
        if not existing.scalars().first():
            await auto_generate_schedules(db, department_id, work_date_from, work_date_to)

    query = select(DoctorSchedule).where(DoctorSchedule.doctor_id > 0)
    if doctor_id:
        query = query.where(DoctorSchedule.doctor_id == doctor_id)
    if department_id:
        doctor_ids_subq = select(Doctor.id).where(
            Doctor.department_id == department_id,
            Doctor.deleted_at.is_(None),
        )
        query = query.where(DoctorSchedule.doctor_id.in_(doctor_ids_subq))
    if work_date_from:
        query = query.where(DoctorSchedule.work_date >= work_date_from)
    if work_date_to:
        query = query.where(DoctorSchedule.work_date <= work_date_to)
    result = await db.execute(query.order_by(DoctorSchedule.work_date, DoctorSchedule.start_time))
    schedules = result.scalars().all()

    # 获取当前患者ID（用于判断是否已预约）
    patient_id: int | None = None
    if current_user.role == 2:
        from app.models.patient import Patient
        pat = (await db.execute(
            select(Patient).where(Patient.user_id == current_user.id, Patient.deleted_at.is_(None))
        )).scalar_one_or_none()
        if pat:
            patient_id = pat.id

    # 计算每个排班的已预约数 + 当前患者是否已预约
    if schedules:
        from app.models.appointment import Appointment

        schedule_ids = [s.id for s in schedules]

        # 批量查询各排班的已预约数
        booked_map: dict[int, int] = {sid: 0 for sid in schedule_ids}
        booked_rows = (await db.execute(
            select(Appointment.schedule_id, func.count(Appointment.id))
            .where(Appointment.schedule_id.in_(schedule_ids), Appointment.status == 1)
            .group_by(Appointment.schedule_id)
        )).all()
        for row in booked_rows:
            booked_map[row[0]] = row[1]

        # 批量查询当前患者已预约的排班
        patient_booked_set: set[int] = set()
        if patient_id is not None:
            patient_rows = (await db.execute(
                select(Appointment.schedule_id)
                .where(Appointment.schedule_id.in_(schedule_ids), Appointment.patient_id == patient_id, Appointment.status == 1)
            )).all()
            patient_booked_set = {row[0] for row in patient_rows}

        return [
            ScheduleOut(
                id=s.id, doctor_id=s.doctor_id,
                work_date=s.work_date, start_time=s.start_time, end_time=s.end_time,
                max_patients=s.max_patients, booked_count=booked_map.get(s.id, 0),
                patient_booked=s.id in patient_booked_set,
                status=s.status,
            ) for s in schedules
        ]

    return []

# ========== 排班 CRUD ==========

@router.post("")
async def create(req: ScheduleCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    schedule = DoctorSchedule(**req.model_dump())
    db.add(schedule)
    await db.flush()
    return {"id": schedule.id, "doctor_id": schedule.doctor_id}

# ========== 模板接口（必须在参数化路由前定义，避免 /templates 被 /{schedule_id} 匹配）==========

@router.get("/templates", response_model=list[ScheduleOut])
async def list_templates(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """获取模板: doctor_id=0 默认模板, doctor_id<0 专属模板。无记录返回空列表"""
    result = await db.execute(
        select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
    )
    return result.scalars().all()

@router.post("/templates")
async def save_template(
    req: TemplateSaveRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    """保存模板: 先删该 doctor_id 的旧模板，再批量插入"""
    await db.execute(
        sqla_delete(DoctorSchedule).where(DoctorSchedule.doctor_id == req.doctor_id)
    )
    for item in req.items:
        db.add(DoctorSchedule(
            doctor_id=req.doctor_id,
            work_date=_make_template_date(item.weekday),
            start_time=time.fromisoformat(item.start_time),
            end_time=time.fromisoformat(item.end_time),
            max_patients=item.max_patients,
            status=1,
        ))
    await db.flush()
    return {"message": "模板已保存", "count": len(req.items)}

@router.delete("/templates")
async def delete_template(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    """删除模板"""
    await db.execute(
        sqla_delete(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
    )
    await db.flush()
    return {"message": "模板已删除"}

# ========== 重新应用模板 ==========

@router.post("/reapply")
async def reapply_template(
    req: ReapplyRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    """删掉指定科室+周的实际排班，按模板重新生成"""
    from app.models.doctor import Doctor
    from app.models.appointment import Appointment

    result = await db.execute(
        select(Doctor.id).where(
            Doctor.department_id == req.department_id,
            Doctor.deleted_at.is_(None),
        )
    )
    doctor_ids = [r[0] for r in result.all()]

    if doctor_ids:
        # 先解除预约关联（FK 约束），再删排班
        schedule_subq = select(DoctorSchedule.id).where(
            DoctorSchedule.doctor_id.in_(doctor_ids),
            DoctorSchedule.work_date >= req.work_date_from,
            DoctorSchedule.work_date <= req.work_date_to,
            DoctorSchedule.doctor_id > 0,
        )
        await db.execute(
            sqla_update(Appointment).where(
                Appointment.schedule_id.in_(schedule_subq)
            ).values(schedule_id=None)
        )
        await db.execute(
            sqla_delete(DoctorSchedule).where(
                DoctorSchedule.doctor_id.in_(doctor_ids),
                DoctorSchedule.work_date >= req.work_date_from,
                DoctorSchedule.work_date <= req.work_date_to,
                DoctorSchedule.doctor_id > 0,
            )
        )
        await db.flush()

    count = await auto_generate_schedules(
        db, req.department_id, req.work_date_from, req.work_date_to
    )
    return {"message": f"已重新生成 {count} 条排班", "count": count}

# ========== 排班更新/删除（参数化路由 /{schedule_id} 放最后，避免匹配到固定路径）==========

@router.put("/{schedule_id}")
async def update(schedule_id: int, req: ScheduleUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(DoctorSchedule).where(DoctorSchedule.id == schedule_id))
    s = result.scalar_one_or_none()
    if s is None: raise HTTPException(status_code=404, detail="排班不存在")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(s, key, val)
    return {"message": "更新成功"}

@router.delete("/{schedule_id}")
async def remove(schedule_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(DoctorSchedule).where(DoctorSchedule.id == schedule_id))
    s = result.scalar_one_or_none()
    if s is None: raise HTTPException(status_code=404, detail="排班不存在")
    await db.delete(s)
    return {"message": "已删除"}
