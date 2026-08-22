from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, DateTime
from app.core.database import Base

class TimestampMixin:
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="修改时间"
    )
