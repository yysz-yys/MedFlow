from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class DoctorCreate(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    name: str = Field(..., max_length=50)
    department_id: int
    title: Optional[str] = None
    introduction: Optional[str] = None

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    title: Optional[str] = None
    introduction: Optional[str] = None

class DoctorOut(BaseModel):
    id: int
    user_id: int
    department_id: int
    name: Optional[str] = None
    title: Optional[str] = None
    introduction: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[str] = None
    class Config:
        from_attributes = True
