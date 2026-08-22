from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class DrugOrderOut(BaseModel):
    id: int; prescription_id: int; total_amount: Optional[Decimal] = None; status: int
    patient_name: Optional[str] = None; doctor_name: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True
