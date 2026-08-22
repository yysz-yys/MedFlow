from sqlalchemy import func, Column, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiagnosisRecord(Base):
    __tablename__ = "diagnosis_record"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    appointment_id = Column(BigInteger, ForeignKey("appointment.id"), nullable=False, unique=True, comment="挂号ID（一对一）")
    doctor_id = Column(BigInteger, ForeignKey("doctor.id"), nullable=False, comment="医生ID")
    patient_id = Column(BigInteger, ForeignKey("patient.id"), nullable=False, comment="病人ID")
    chief_complaint = Column(String(500), comment="主诉")
    diagnosis_result = Column(String(500), comment="诊断结果")
    prescription_advice = Column(String(500), comment="医嘱")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    appointment = relationship("Appointment", lazy="joined")
    doctor = relationship("Doctor", lazy="joined")
    patient = relationship("Patient", lazy="joined")
