from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db; from app.core.deps import require_role, get_current_user
from app.models.diagnosis_record import DiagnosisRecord
from app.models.doctor import Doctor; from app.models.patient import Patient
from app.models.user import User
from app.schemas.diagnosis_record import DiagnosisCreate, DiagnosisUpdate, DiagnosisOut
from app.services.diagnosis_service import create_diagnosis, update_diagnosis

router = APIRouter(prefix="/diagnosis-records", tags=["诊断记录"])

@router.get("", response_model=list[DiagnosisOut])
async def list_diagnosis(patient_id: int = None, doctor_id: int = None,
                         current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(DiagnosisRecord)
    if current_user.role == 0: pass
    elif current_user.role == 1:
        result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        dr = result.scalar_one_or_none()
        if dr: query = query.where(DiagnosisRecord.doctor_id == dr.id)
        else: return []
    else:
        result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
        pt = result.scalar_one_or_none()
        if pt: query = query.where(DiagnosisRecord.patient_id == pt.id)
        else: return []
    if patient_id: query = query.where(DiagnosisRecord.patient_id == patient_id)
    if doctor_id: query = query.where(DiagnosisRecord.doctor_id == doctor_id)
    records = (await db.execute(query.order_by(DiagnosisRecord.created_at.desc()))).scalars().all()
    result = []
    for record in records:
        pt_name = (await db.execute(select(User.name).where(User.id == record.patient.user_id))).scalar_one_or_none()
        dr_name = (await db.execute(select(User.name).where(User.id == record.doctor.user_id))).scalar_one_or_none()
        dept_name = record.appointment.department.name if record.appointment and record.appointment.department else None
        result.append({**record.__dict__, 'patient_name': pt_name, 'doctor_name': dr_name, 'department_name': dept_name})
    return result

@router.get("/{dr_id}", response_model=DiagnosisOut)
async def get_diagnosis(dr_id: int, current_user=Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    dr = (await db.execute(select(DiagnosisRecord).where(DiagnosisRecord.id == dr_id))).scalar_one_or_none()
    if dr is None: raise HTTPException(status_code=404)
    if current_user.role == 0: pass
    elif current_user.role == 1:
        if dr.doctor_id != (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none().id:
            raise HTTPException(status_code=403, detail="无权查看")
    else:
        pt = (await db.execute(select(Patient).where(Patient.user_id == current_user.id))).scalar_one_or_none()
        if not pt or dr.patient_id != pt.id:
            raise HTTPException(status_code=403, detail="无权查看")
    pt_name = (await db.execute(select(User.name).where(User.id == dr.patient.user_id))).scalar_one_or_none()
    dr_name = (await db.execute(select(User.name).where(User.id == dr.doctor.user_id))).scalar_one_or_none()
    dept_name = dr.appointment.department.name if dr.appointment and dr.appointment.department else None
    return {**dr.__dict__, 'patient_name': pt_name, 'doctor_name': dr_name, 'department_name': dept_name}

@router.post("")
async def create(req: DiagnosisCreate, current_user=Depends(require_role([1])),
                 db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if doctor is None: raise HTTPException(status_code=400, detail="医生档案不存在")
    dr = await create_diagnosis(db, req.appointment_id, doctor.id,
        req.chief_complaint, req.diagnosis_result, req.prescription_advice)
    return {"id": dr.id, "appointment_id": dr.appointment_id}

@router.put("/{dr_id}")
async def update(dr_id: int, req: DiagnosisUpdate, current_user=Depends(require_role([1])),
                 db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if doctor is None: raise HTTPException(status_code=400)
    return await update_diagnosis(db, dr_id, doctor.id,
        req.chief_complaint, req.diagnosis_result, req.prescription_advice)
