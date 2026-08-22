from pydantic import BaseModel, Field
from typing import Optional


class DataDictCreate(BaseModel):
    dict_type: str = Field(..., max_length=50)
    dict_key: int = Field(...)
    dict_label: str = Field(..., max_length=50)
    sort_order: int = 0


class DataDictUpdate(BaseModel):
    dict_label: Optional[str] = None
    sort_order: Optional[int] = None


class DataDictOut(BaseModel):
    id: int
    dict_type: str
    dict_key: int
    dict_label: str
    sort_order: int

    class Config:
        from_attributes = True
