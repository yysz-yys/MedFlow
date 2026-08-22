from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class DrugCreate(BaseModel):
    name: str = Field(..., max_length=100)
    specification: Optional[str] = None
    unit: Optional[str] = None
    price: Decimal
    stock: int = Field(..., ge=0)
    manufacturer: Optional[str] = None

class DrugUpdate(BaseModel):
    name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = Field(None, ge=0)
    manufacturer: Optional[str] = None

class DrugStockUpdate(BaseModel):
    change: int  # 正数增加，负数减少

class DrugOut(BaseModel):
    id: int
    name: str
    specification: Optional[str] = None
    unit: Optional[str] = None
    price: Decimal
    stock: int
    manufacturer: Optional[str] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    class Config:
        from_attributes = True
