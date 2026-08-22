from sqlalchemy import func, Column, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Prescription(Base):
    __tablename__ = "prescription"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    diagnosis_id = Column(BigInteger, ForeignKey("diagnosis_record.id"), nullable=False, unique=True, comment="诊断记录ID（一对一）")
    doctor_id = Column(BigInteger, ForeignKey("doctor.id"), nullable=False, comment="医生ID")
    patient_id = Column(BigInteger, ForeignKey("patient.id"), nullable=False, comment="病人ID")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    diagnosis_record = relationship("DiagnosisRecord", lazy="joined")
    doctor = relationship("Doctor", lazy="joined")
    patient = relationship("Patient", lazy="joined")
