from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AppointmentCreate(BaseModel):
    doctor_id: int
    schedule_id: int

class AppointmentUpdate(BaseModel):
    doctor_id: Optional[int] = None
    schedule_id: Optional[int] = None

class AppointmentOut(BaseModel):
    id: int; patient_id: int; doctor_id: int; department_id: int
    patient_name: Optional[str] = None; doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    appointment_time: Optional[str] = None; status: int
    schedule_start_time: Optional[str] = None
    schedule_end_time: Optional[str] = None
    schedule_max_patients: Optional[int] = None
    schedule_booked_count: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True
