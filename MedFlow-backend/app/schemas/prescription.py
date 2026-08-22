from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

class PrescriptionItemIn(BaseModel):
    drug_id: int
    quantity: int = Field(..., ge=1)
    usage_method: Optional[str] = None
    days: Optional[int] = None

class PrescriptionCreate(BaseModel):
    diagnosis_id: int
    items: List[PrescriptionItemIn]

class PrescriptionUpdate(BaseModel):
    items: List[PrescriptionItemIn]

class PrescriptionItemOut(BaseModel):
    id: int; drug_id: int; drug_name: Optional[str] = None
    specification: Optional[str] = None; unit: Optional[str] = None
    quantity: int; usage_method: Optional[str] = None; days: Optional[int] = None
    class Config: from_attributes = True

class PrescriptionOut(BaseModel):
    id: int; diagnosis_id: int; doctor_id: int; patient_id: int
    items: List[PrescriptionItemOut] = []
    created_at: Optional[datetime] = None
    class Config: from_attributes = True
