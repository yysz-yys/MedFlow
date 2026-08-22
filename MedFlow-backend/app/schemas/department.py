from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from .common import BaseResponse

class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

class DepartmentOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    class Config:
        from_attributes = True
