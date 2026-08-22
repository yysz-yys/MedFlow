from sqlalchemy import func, Column, String, BigInteger, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notification"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, nullable=False, comment="接收人ID")
    title = Column(String(100), nullable=False, comment="标题")
    content = Column(String(500), nullable=False, comment="内容")
    type = Column(String(30), nullable=False, comment="通知分类")
    is_read = Column(TINYINT, nullable=False, default=0, comment="已读状态：0=未读 / 1=已读")
    related_type = Column(String(50), comment="关联对象类型")
    related_id = Column(BigInteger, comment="关联对象ID")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="发送时间")
