from sqlalchemy import func, Column, BigInteger, ForeignKey, DECIMAL, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.core.database import Base

class DrugOrder(Base):
    __tablename__ = "drug_order"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    prescription_id = Column(BigInteger, ForeignKey("prescription.id"), nullable=False, unique=True, comment="处方ID（一对一）")
    total_amount = Column(DECIMAL(10, 2), comment="总金额")
    status = Column(TINYINT, nullable=False, default=1, comment="状态：0=已取消 / 1=待取药 / 2=已取药")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    prescription = relationship("Prescription", lazy="joined")
