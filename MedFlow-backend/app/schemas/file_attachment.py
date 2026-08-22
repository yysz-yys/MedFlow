from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FileOut(BaseModel):
    id: int; file_name: str; file_type: Optional[str] = None
    file_size: Optional[int] = None; created_at: Optional[datetime] = None

    class Config: from_attributes = True
