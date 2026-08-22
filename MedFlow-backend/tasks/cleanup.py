from sqlalchemy import delete
from datetime import datetime, timezone, timedelta
from app.core.database import async_session
from app.models.verification_code import VerificationCode
from app.models.token_blacklist import TokenBlacklist
from app.models.audit_log import AuditLog
from app.core.config import get_settings

settings = get_settings()


async def cleanup_task():
    async with async_session() as db:
        now = datetime.now(timezone.utc)
        await db.execute(delete(VerificationCode).where(VerificationCode.expires_at < now))
        await db.execute(delete(TokenBlacklist).where(TokenBlacklist.expires_at < now))
        cutoff = now - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
        await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
        await db.commit()
