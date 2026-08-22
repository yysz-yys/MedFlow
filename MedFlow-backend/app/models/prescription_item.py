from sqlalchemy import func, Column, BigInteger, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class PrescriptionItem(Base):
    __tablename__ = "prescription_item"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    prescription_id = Column(BigInteger, ForeignKey("prescription.id"), nullable=False, comment="处方ID")
    drug_id = Column(BigInteger, ForeignKey("drug.id"), nullable=False, comment="药品ID")
    quantity = Column(Integer, nullable=False, comment="数量")
    usage_method = Column(String(100), comment="用法")
    days = Column(Integer, comment="天数")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    drug = relationship("Drug", lazy="joined")
