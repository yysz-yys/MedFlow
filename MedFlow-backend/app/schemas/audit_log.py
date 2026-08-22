from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class AuditLogOut(BaseModel):
    id: int; user_id: Optional[int] = None; user_name: Optional[str] = None
    role: Optional[int] = None; action: str; target_type: Optional[str] = None
    target_id: Optional[int] = None; detail: Optional[str] = None
    ip_address: Optional[str] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True
