from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DiagnosisRecordItem(BaseModel):
    id: int
    chief_complaint: Optional[str] = None
    diagnosis_result: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class DoctorPatientOut(BaseModel):
    id: int
    name: Optional[str] = None
    gender: Optional[int] = None
    birth_date: Optional[str] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergy_history: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    last_diagnosis_at: Optional[str] = None
    diagnosis_records: list[DiagnosisRecordItem] = []

    class Config:
        from_attributes = True
