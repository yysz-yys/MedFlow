from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time

class ScheduleCreate(BaseModel):
    doctor_id: int
    work_date: date
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    max_patients: int = Field(default=10, ge=1)

class ScheduleUpdate(BaseModel):
    work_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    max_patients: Optional[int] = None
    status: Optional[int] = Field(None, ge=0, le=1)

from datetime import datetime as dt
class ScheduleOut(BaseModel):
    id: int
    doctor_id: int
    work_date: date
    start_time: time
    end_time: time
    max_patients: int
    booked_count: int = 0
    patient_booked: bool = False
    status: int
    class Config:
        from_attributes = True

class TemplateSlot(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    max_patients: int = Field(default=20, ge=1)

class TemplateSaveRequest(BaseModel):
    doctor_id: int
    items: list[TemplateSlot]

class ReapplyRequest(BaseModel):
    department_id: int
    work_date_from: date
    work_date_to: date
