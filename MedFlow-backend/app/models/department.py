from sqlalchemy import func, Column, String, BigInteger, DateTime
from app.core.database import Base

class Department(Base):
    __tablename__ = "department"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")
    description = Column(String(255), comment="描述")
    deleted_at = Column(DateTime, comment="软删除时间（NULL=正常）")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
