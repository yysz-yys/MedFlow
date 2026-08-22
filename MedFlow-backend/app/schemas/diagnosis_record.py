from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class DiagnosisCreate(BaseModel):
    appointment_id: int
    chief_complaint: Optional[str] = None
    diagnosis_result: Optional[str] = None
    prescription_advice: Optional[str] = None

class DiagnosisUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    diagnosis_result: Optional[str] = None
    prescription_advice: Optional[str] = None

class DiagnosisOut(BaseModel):
    id: int; appointment_id: int; doctor_id: int; patient_id: int
    chief_complaint: Optional[str] = None; diagnosis_result: Optional[str] = None
    prescription_advice: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    patient_name: Optional[str] = None; doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    class Config: from_attributes = True
