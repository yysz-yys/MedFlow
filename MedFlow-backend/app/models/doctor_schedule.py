from sqlalchemy import func, Column, BigInteger, Date, Time, Integer, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class DoctorSchedule(Base):
    __tablename__ = "doctor_schedule"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    doctor_id = Column(BigInteger, nullable=False, comment="医生ID；0=默认模板，负数(x)表示医生-x的专属模板，正数=实际排班记录")
    work_date = Column(Date, nullable=False, comment="出诊日期")
    start_time = Column(Time, nullable=False, comment="开始时间")
    end_time = Column(Time, nullable=False, comment="结束时间")
    max_patients = Column(Integer, nullable=False, default=10, comment="该时段最大挂号数")
    status = Column(TINYINT, nullable=False, default=1, comment="状态：0=停诊 / 1=可预约")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
