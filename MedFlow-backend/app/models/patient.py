from sqlalchemy import func, Column, String, BigInteger, ForeignKey, Date, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patient"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, unique=True, comment="用户ID（一对一）")
    gender = Column(TINYINT, comment="性别：0=未知 / 1=男 / 2=女")
    birth_date = Column(Date, comment="出生日期")
    address = Column(String(255), comment="居住地址")
    blood_type = Column(String(10), comment="血型")
    allergy_history = Column(String(500), comment="过敏史")
    deleted_at = Column(DateTime, comment="软删除时间")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    user = relationship("User", lazy="joined")
