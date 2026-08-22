from sqlalchemy import func, Column, String, BigInteger, DateTime
from app.core.database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    token_jti = Column(String(100), nullable=False, unique=True, comment="JWT jti")
    user_id = Column(BigInteger, nullable=False, comment="所属用户ID")
    expires_at = Column(DateTime, nullable=False, comment="原始过期时间")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="拉黑时间")
