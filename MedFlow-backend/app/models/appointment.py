from sqlalchemy import func, Column, BigInteger, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.core.database import Base

class Appointment(Base):
    __tablename__ = "appointment"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    patient_id = Column(BigInteger, ForeignKey("patient.id"), nullable=False, comment="病人ID")
    doctor_id = Column(BigInteger, ForeignKey("doctor.id"), nullable=False, comment="医生ID")
    department_id = Column(BigInteger, ForeignKey("department.id"), nullable=False, comment="科室ID")
    schedule_id = Column(BigInteger, ForeignKey("doctor_schedule.id"), nullable=True, comment="排班ID")
    appointment_time = Column(DateTime, comment="预约就诊时间")
    status = Column(TINYINT, nullable=False, default=1, comment="状态：0=已取消 / 1=待就诊 / 2=已就诊")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
    patient = relationship("Patient", lazy="joined")
    doctor = relationship("Doctor", lazy="joined")
    department = relationship("Department", lazy="joined")
    schedule = relationship("DoctorSchedule", lazy="joined")
