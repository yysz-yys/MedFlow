from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.models.doctor import Doctor
from app.models.department import Department
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut
from app.schemas.common import PageResponse
from app.schemas.doctor_patient import DoctorPatientOut, DiagnosisRecordItem
from app.models.patient import Patient
from app.models.diagnosis_record import DiagnosisRecord
from app.models.file_attachment import FileAttachment
from datetime import datetime, timezone

router = APIRouter(prefix="/doctors", tags=["医生"])

@router.get("", response_model=PageResponse[DoctorOut])
async def list_doctors(department_id: int = None, keyword: str = None,
                       page: int = 1, page_size: int = 10,
                       sort_by: str = None, sort_order: str = None,
                       db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    base = select(Doctor).join(Doctor.user).outerjoin(Doctor.department)
    # 医生只能看自己的档案
    if current_user.role == 1:
        base = base.where(Doctor.user_id == current_user.id)
    if department_id:
        base = base.where(Doctor.department_id == department_id)
    if keyword:
        base = base.where(User.name.contains(keyword) | Doctor.title.contains(keyword))
    if sort_by and sort_by in {'id', 'name', 'title', 'department_name', 'created_at', 'deleted_at'}:
        if sort_by == 'name':
            col = literal_column("CONVERT(`user`.`name` USING gbk)")
        elif sort_by == 'title':
            col = literal_column("CONVERT(`doctor`.`title` USING gbk)")
        elif sort_by == 'department_name':
            col = literal_column("CONVERT(`department`.`name` USING gbk)")
        else:
            col = getattr(Doctor, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        base = base.order_by(col)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    query = base.options(joinedload(Doctor.user), joinedload(Doctor.department))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    doctors = result.scalars().all()
    items = [
        DoctorOut(
            id=d.id, user_id=d.user_id, department_id=d.department_id,
            name=d.user.name, title=d.title, introduction=d.introduction,
            department_name=d.department.name if d.department else None,
            created_at=d.created_at.isoformat() if d.created_at else None,
            deleted_at=d.deleted_at.isoformat() if d.deleted_at else None,
        )
        for d in doctors
    ]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)

@router.post("", response_model=DoctorOut)
async def create_doctor(req: DoctorCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    # 先检查邮箱
    existing = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    user = User(email=req.email, password=hash_password(req.password), name=req.name, role=1)
    db.add(user)
    await db.flush()
    doctor = Doctor(user_id=user.id, department_id=req.department_id, title=req.title, introduction=req.introduction)
    db.add(doctor)
    await db.flush()
    return DoctorOut(id=doctor.id, user_id=user.id, department_id=doctor.department_id, name=user.name, title=doctor.title, introduction=doctor.introduction)

@router.put("/{doctor_id}")
async def update_doctor(doctor_id: int, req: DoctorUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id, Doctor.deleted_at.is_(None)))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=404, detail="医生不存在")
    # 只有管理员或医生本人可以修改
    if current_user.role != 0 and current_user.id != doctor.user_id:
        raise HTTPException(status_code=403)
    if req.name is not None:
        doctor.user.name = req.name
    # 科室只允许管理员修改
    if req.department_id is not None and current_user.role == 0:
        doctor.department_id = req.department_id
    if req.title is not None:
        doctor.title = req.title
    if req.introduction is not None:
        doctor.introduction = req.introduction
    return {"message": "更新成功"}

@router.delete("/{doctor_id}")
async def soft_delete_doctor(doctor_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Doctor).options(joinedload(Doctor.user)).where(Doctor.id == doctor_id, Doctor.deleted_at.is_(None)))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=404, detail="医生不存在")
    doctor.deleted_at = datetime.now(timezone.utc)
    doctor.user.status = 0
    return {"message": "已删除"}

@router.put("/{doctor_id}/restore")
async def restore_doctor(doctor_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Doctor).options(joinedload(Doctor.user)).where(Doctor.id == doctor_id, Doctor.deleted_at.isnot(None)))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=404, detail="医生不存在或未被删除")
    doctor.deleted_at = None
    doctor.user.status = 1
    return {"message": "已恢复"}


@router.get("/me/patients", response_model=PageResponse[DoctorPatientOut])
async def list_my_patients(
    keyword: str = None,
    gender: int = None,
    page: int = 1,
    page_size: int = 10,
    current_user=Depends(require_role([1])),
    db: AsyncSession = Depends(get_db),
):
    # 查出当前医生的 doctor_id
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=400, detail="医生档案不存在")

    # 子查询：该医生所有诊断记录，按 patient_id 去重，取最近诊断时间
    diag_sub = (
        select(
            DiagnosisRecord.patient_id,
            func.max(DiagnosisRecord.created_at).label("last_diagnosis_at"),
        )
        .where(DiagnosisRecord.doctor_id == doctor.id)
        .group_by(DiagnosisRecord.patient_id)
        .subquery()
    )

    # 主查询：join Patient + User，按最近诊断时间倒序
    base = (
        select(Patient, diag_sub.c.last_diagnosis_at)
        .join(diag_sub, Patient.id == diag_sub.c.patient_id)
        .join(Patient.user)
        .where(Patient.deleted_at.is_(None))
    )

    if keyword:
        kw = f"%{keyword}%"
        base = base.where(
            User.name.contains(kw) | User.phone.contains(kw)
        )
    if gender is not None:
        base = base.where(Patient.gender == gender)

    # 分页
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar()

    rows = (
        await db.execute(
            base.order_by(diag_sub.c.last_diagnosis_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    # 收集所有 patient_id 用于批量查诊断记录
    patient_ids = [row[0].id for row in rows]

    # 批量获取该医生对这些病人的所有诊断记录
    diag_query = (
        select(DiagnosisRecord)
        .where(
            DiagnosisRecord.doctor_id == doctor.id,
            DiagnosisRecord.patient_id.in_(patient_ids),
        )
        .order_by(DiagnosisRecord.created_at.desc())
    )
    diag_rows = (await db.execute(diag_query)).scalars().all()

    # 按 patient_id 分组
    diag_map: dict = {}
    for d in diag_rows:
        diag_map.setdefault(d.patient_id, []).append(d)

    # 批量查询患者头像（file_attachment 表，related_type="avatar"，related_id 为用户ID）
    user_ids = [row[0].user_id for row in rows]
    avatar_query = (
        select(FileAttachment)
        .where(
            FileAttachment.related_type == "avatar",
            FileAttachment.related_id.in_(user_ids),
        )
        .order_by(FileAttachment.created_at.desc())
    )
    avatar_rows = (await db.execute(avatar_query)).scalars().all()
    avatar_map: dict = {}
    for fa in avatar_rows:
        if fa.related_id not in avatar_map:
            avatar_map[fa.related_id] = fa.file_path

    items = []
    for patient, last_at in rows:
        records = [
            DiagnosisRecordItem(
                id=r.id,
                chief_complaint=r.chief_complaint,
                diagnosis_result=r.diagnosis_result,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in diag_map.get(patient.id, [])
        ]
        items.append(
            DoctorPatientOut(
                id=patient.id,
                name=patient.user.name,
                gender=patient.gender,
                birth_date=patient.birth_date.isoformat() if patient.birth_date else None,
                address=patient.address,
                blood_type=patient.blood_type,
                allergy_history=patient.allergy_history,
                phone=patient.user.phone,
                avatar=avatar_map.get(patient.user_id),
                last_diagnosis_at=last_at.isoformat() if last_at else None,
                diagnosis_records=records,
            )
        )

    return PageResponse(total=total, page=page, page_size=page_size, items=items)
