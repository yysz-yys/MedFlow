from sqlalchemy import func, Column, String, BigInteger, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class VerificationCode(Base):
    __tablename__ = "verification_code"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    target = Column(String(100), nullable=False, comment="接收方")
    code = Column(String(10), nullable=False, comment="验证码")
    scene = Column(String(30), nullable=False, comment="使用场景")
    send_ip = Column(String(45), comment="发送IP")
    attempt_count = Column(TINYINT, nullable=False, default=0, comment="校验失败次数")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    used = Column(TINYINT, nullable=False, default=0, comment="是否已使用")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="发送时间")
