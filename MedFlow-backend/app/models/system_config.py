from sqlalchemy import func, Column, String, BigInteger, DateTime
from app.core.database import Base

class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    config_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    config_value = Column(String(500), comment="配置值")
    description = Column(String(255), comment="说明")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
