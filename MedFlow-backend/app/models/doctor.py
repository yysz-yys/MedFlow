from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Doctor(Base):
    __tablename__ = "doctor"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, unique=True, comment="用户ID（一对一）")
    department_id = Column(BigInteger, ForeignKey("department.id"), comment="科室ID（多对一，注册时未分配）")
    title = Column(String(50), comment="职称")
    introduction = Column(String(500), comment="简介")
    deleted_at = Column(DateTime, comment="软删除时间")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    user = relationship("User", lazy="joined")
    department = relationship("Department", lazy="joined")
