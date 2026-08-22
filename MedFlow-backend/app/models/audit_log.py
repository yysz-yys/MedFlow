from sqlalchemy import func, Column, String, BigInteger, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, comment="操作人ID")
    user_name = Column(String(50), comment="操作人姓名")
    role = Column(TINYINT, comment="操作人角色")
    action = Column(String(50), nullable=False, comment="操作类型")
    target_type = Column(String(50), comment="操作对象类型")
    target_id = Column(BigInteger, comment="操作对象ID")
    old_value = Column(String(500), comment="修改前的值")
    new_value = Column(String(500), comment="修改后的值")
    detail = Column(String(500), comment="操作详情")
    ip_address = Column(String(45), comment="操作IP")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="操作时间")
