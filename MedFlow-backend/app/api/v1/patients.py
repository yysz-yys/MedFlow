from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.core.security import hash_password
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate, PatientOut
from app.schemas.common import PageResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/patients", tags=["病人"])

@router.get("", response_model=PageResponse[PatientOut])
async def list_patients(keyword: str = None, gender: int = None, blood_type: str = None,
                        page: int = 1, page_size: int = 10,
                        sort_by: str = None, sort_order: str = None,
                        db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    base = select(Patient).join(Patient.user)
    # 病人只能看自己的档案
    if current_user.role == 2:
        base = base.where(Patient.user_id == current_user.id)
    if keyword:
        base = base.where(User.name.contains(keyword) | Patient.address.contains(keyword))
    if gender is not None:
        base = base.where(Patient.gender == gender)
    if blood_type is not None:
        base = base.where(Patient.blood_type == blood_type)
    if sort_by and sort_by in {'id', 'name', 'gender', 'birth_date', 'blood_type', 'created_at', 'deleted_at'}:
        if sort_by == 'name':
            col = literal_column("CONVERT(`user`.`name` USING gbk)")
        else:
            col = getattr(Patient, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        base = base.order_by(col)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    query = base.options(joinedload(Patient.user)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    patients = result.scalars().all()
    items = [PatientOut(id=p.id, user_id=p.user_id, name=p.user.name, gender=p.gender,
                        birth_date=p.birth_date.isoformat() if p.birth_date else None,
                        address=p.address, blood_type=p.blood_type, allergy_history=p.allergy_history,
                        created_at=p.created_at.isoformat() if p.created_at else None,
                        deleted_at=p.deleted_at.isoformat() if p.deleted_at else None)
             for p in patients]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)

@router.post("", response_model=PatientOut)
async def create_patient(req: PatientCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    existing = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    user = User(email=req.email, password=hash_password(req.password), name=req.name, role=2)
    db.add(user)
    await db.flush()
    patient = Patient(
        user_id=user.id,
        gender=req.gender,
        birth_date=req.birth_date,
        address=req.address,
        blood_type=req.blood_type,
        allergy_history=req.allergy_history,
    )
    db.add(patient)
    await db.flush()
    return PatientOut(id=patient.id, user_id=user.id, name=user.name, gender=patient.gender,
                      birth_date=patient.birth_date.isoformat() if patient.birth_date else None,
                      address=patient.address, blood_type=patient.blood_type,
                      allergy_history=patient.allergy_history)

@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Patient).options(joinedload(Patient.user)).where(Patient.id == patient_id, Patient.deleted_at.is_(None))
    )
    patient = result.scalar_one_or_none()
    if patient is None: raise HTTPException(status_code=404, detail="病人不存在")
    # 本人 / 该病人的医生 / 管理员
    if current_user.role == 2 and current_user.id != patient.user_id:
        # 检查是否是挂过号的医生
        from app.models.appointment import Appointment
        apt = (await db.execute(select(Appointment).where(Appointment.patient_id == patient.id, Appointment.doctor.has(user_id=current_user.id)))).scalar_one_or_none()
        if apt is None and current_user.role != 0:
            raise HTTPException(status_code=403, detail="无权查看")
    return PatientOut(id=patient.id, user_id=patient.user_id, name=patient.user.name, gender=patient.gender,
                      birth_date=patient.birth_date.isoformat() if patient.birth_date else None,
                      address=patient.address, blood_type=patient.blood_type, allergy_history=patient.allergy_history)

@router.put("/{patient_id}")
async def update_patient(patient_id: int, req: PatientUpdate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id, Patient.deleted_at.is_(None)))
    patient = result.scalar_one_or_none()
    if patient is None: raise HTTPException(status_code=404, detail="不存在")
    if current_user.role != 0 and current_user.id != patient.user_id:
        raise HTTPException(status_code=403)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(patient, k, v)
    return {"message": "更新成功"}

@router.delete("/{patient_id}")
async def soft_delete(patient_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Patient).options(joinedload(Patient.user)).where(Patient.id == patient_id, Patient.deleted_at.is_(None)))
    patient = result.scalar_one_or_none()
    if patient is None: raise HTTPException(status_code=404)
    patient.deleted_at = datetime.now(timezone.utc)
    patient.user.status = 0
    return {"message": "已删除"}

@router.put("/{patient_id}/restore")
async def restore(patient_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Patient).options(joinedload(Patient.user)).where(Patient.id == patient_id, Patient.deleted_at.isnot(None)))
    patient = result.scalar_one_or_none()
    if patient is None: raise HTTPException(status_code=404, detail="病人不存在或未被删除")
    patient.deleted_at = None
    patient.user.status = 1
    return {"message": "已恢复"}
