from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class NotificationCreate(BaseModel):
    title: str
    content: str
    type: str = "SYSTEM"  # SYSTEM 公告 / 其他类型后端自动生成
    user_id: Optional[int] = None  # 不填=全员，填了=指定用户

class NotificationOut(BaseModel):
    id: int; title: str; content: str; type: str; is_read: int
    related_type: Optional[str] = None; related_id: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class NotificationAdminItem(BaseModel):
    id: int
    title: str
    content: str
    type: str
    recipient_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
