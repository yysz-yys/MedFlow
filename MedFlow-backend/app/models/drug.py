from sqlalchemy import func, Column, String, BigInteger, Integer, DECIMAL, DateTime
from app.core.database import Base

class Drug(Base):
    __tablename__ = "drug"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="名称")
    specification = Column(String(50), comment="规格")
    unit = Column(String(20), comment="单位")
    price = Column(DECIMAL(10, 2), nullable=False, comment="单价")
    stock = Column(Integer, nullable=False, comment="库存数量")
    manufacturer = Column(String(100), comment="生产厂商")
    deleted_at = Column(DateTime, comment="软删除时间")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
