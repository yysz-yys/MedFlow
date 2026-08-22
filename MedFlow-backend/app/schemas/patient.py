from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class PatientCreate(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    name: str = Field(..., max_length=50)
    gender: Optional[int] = Field(None, ge=0, le=2)
    birth_date: Optional[date] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergy_history: Optional[str] = None

class PatientUpdate(BaseModel):
    gender: Optional[int] = Field(None, ge=0, le=2)
    birth_date: Optional[date] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergy_history: Optional[str] = None

class PatientOut(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    gender: Optional[int] = None
    birth_date: Optional[str] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergy_history: Optional[str] = None
    created_at: Optional[str] = None
    deleted_at: Optional[str] = None
    class Config:
        from_attributes = True
