from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.appointment import Appointment
from app.models.diagnosis_record import DiagnosisRecord
from app.models.doctor import Doctor

async def create_diagnosis(db: AsyncSession, appointment_id: int, doctor_id: int,
                           chief_complaint: str, diagnosis_result: str, prescription_advice: str):
    apt = (await db.execute(select(Appointment).where(Appointment.id == appointment_id))).scalar_one_or_none()
    if apt is None: raise HTTPException(status_code=404, detail="挂号不存在")
    if apt.status != 2: raise HTTPException(status_code=400, detail="请先完成就诊再写诊断")
    if apt.doctor_id != doctor_id: raise HTTPException(status_code=403, detail="只能诊断自己的挂号")

    existing = (await db.execute(
        select(DiagnosisRecord).where(DiagnosisRecord.appointment_id == appointment_id)
    )).scalar_one_or_none()
    if existing: raise HTTPException(status_code=400, detail="该挂号已有诊断记录")

    dr = DiagnosisRecord(appointment_id=appointment_id, doctor_id=doctor_id,
                         patient_id=apt.patient_id, chief_complaint=chief_complaint,
                         diagnosis_result=diagnosis_result, prescription_advice=prescription_advice)
    db.add(dr)
    await db.flush()

    from app.services.notification_service import create_notification
    from app.models.patient import Patient
    patient = (await db.execute(select(Patient).where(Patient.id == apt.patient_id))).scalar_one()
    await create_notification(db, patient.user_id, "诊断完成",
        "医生已完成您的诊断，请查收处方", "DISPENSE", "diagnosis_record", dr.id)
    return dr

async def update_diagnosis(db: AsyncSession, diagnosis_id: int, doctor_id: int,
                           chief_complaint: str = None, diagnosis_result: str = None,
                           prescription_advice: str = None):
    dr = (await db.execute(select(DiagnosisRecord).where(DiagnosisRecord.id == diagnosis_id))).scalar_one_or_none()
    if dr is None: raise HTTPException(status_code=404)
    if dr.doctor_id != doctor_id: raise HTTPException(status_code=403, detail="只能修改自己的诊断")
    old_value = {"chief_complaint": dr.chief_complaint, "diagnosis_result": dr.diagnosis_result,
                 "prescription_advice": dr.prescription_advice}
    if chief_complaint is not None: dr.chief_complaint = chief_complaint
    if diagnosis_result is not None: dr.diagnosis_result = diagnosis_result
    if prescription_advice is not None: dr.prescription_advice = prescription_advice
    import json
    return {"old_value": json.dumps(old_value), "new_value": json.dumps(
        {"chief_complaint": dr.chief_complaint, "diagnosis_result": dr.diagnosis_result,
         "prescription_advice": dr.prescription_advice})}
