from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db; from app.core.deps import require_role, get_current_user
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.models.doctor import Doctor; from app.models.patient import Patient
from app.models.drug import Drug
from app.schemas.prescription import (PrescriptionCreate, PrescriptionUpdate,
    PrescriptionOut, PrescriptionItemOut)
from app.services.prescription_service import create_prescription, update_prescription

router = APIRouter(prefix="/prescriptions", tags=["处方"])

@router.get("", response_model=list[PrescriptionOut])
async def list_prescriptions(current_user=Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    query = select(Prescription)
    if current_user.role == 0: pass
    elif current_user.role == 1:
        doctor = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
        if doctor: query = query.where(Prescription.doctor_id == doctor.id)
        else: return []
    else:
        patient = (await db.execute(select(Patient).where(Patient.user_id == current_user.id))).scalar_one_or_none()
        if patient: query = query.where(Prescription.patient_id == patient.id)
        else: return []
    prescriptions = (await db.execute(query.order_by(Prescription.created_at.desc()))).scalars().all()
    result = []
    for p in prescriptions:
        items = (await db.execute(select(PrescriptionItem).options(
            joinedload(PrescriptionItem.drug)).where(PrescriptionItem.prescription_id == p.id))).scalars().all()
        result.append(PrescriptionOut(id=p.id, diagnosis_id=p.diagnosis_id,
            doctor_id=p.doctor_id, patient_id=p.patient_id,
            items=[PrescriptionItemOut(id=i.id, drug_id=i.drug_id,
                drug_name=i.drug.name,
                specification=i.drug.specification, unit=i.drug.unit,
                quantity=i.quantity,
                usage_method=i.usage_method, days=i.days) for i in items],
            created_at=p.created_at.isoformat() if p.created_at else None))
    return result

@router.get("/{prescription_id}", response_model=PrescriptionOut)
async def get_prescription(prescription_id: int, current_user=Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Prescription).where(Prescription.id == prescription_id))).scalar_one_or_none()
    if p is None: raise HTTPException(status_code=404)
    if current_user.role == 0: pass
    elif current_user.role == 1:
        doctor = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
        if not doctor or p.doctor_id != doctor.id: raise HTTPException(status_code=403)
    else:
        patient = (await db.execute(select(Patient).where(Patient.user_id == current_user.id))).scalar_one_or_none()
        if not patient or p.patient_id != patient.id: raise HTTPException(status_code=403)
    items = (await db.execute(select(PrescriptionItem).options(
        joinedload(PrescriptionItem.drug)).where(PrescriptionItem.prescription_id == p.id))).scalars().all()
    return PrescriptionOut(id=p.id, diagnosis_id=p.diagnosis_id,
        doctor_id=p.doctor_id, patient_id=p.patient_id,
        items=[PrescriptionItemOut(id=i.id, drug_id=i.drug_id,
            drug_name=i.drug.name,
            specification=i.drug.specification, unit=i.drug.unit,
            quantity=i.quantity,
            usage_method=i.usage_method, days=i.days) for i in items],
        created_at=p.created_at.isoformat() if p.created_at else None)

@router.post("")
async def create(req: PrescriptionCreate, current_user=Depends(require_role([1])),
                 db: AsyncSession = Depends(get_db)):
    doctor = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
    if doctor is None: raise HTTPException(status_code=400, detail="医生档案不存在")
    return await create_prescription(db, req.diagnosis_id, doctor.id,
        [i.model_dump() for i in req.items])

@router.put("/{prescription_id}")
async def update(prescription_id: int, req: PrescriptionUpdate,
                 current_user=Depends(require_role([1])), db: AsyncSession = Depends(get_db)):
    doctor = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
    if doctor is None: raise HTTPException(status_code=400)
    return await update_prescription(db, prescription_id, doctor.id,
        [i.model_dump() for i in req.items])
