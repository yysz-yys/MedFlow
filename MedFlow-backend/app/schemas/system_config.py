from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ConfigCreate(BaseModel):
    config_key: str = Field(..., max_length=100)
    config_value: Optional[str] = None
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None


class ConfigOut(BaseModel):
    id: int
    config_key: str
    config_value: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
