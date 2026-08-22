from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db; from app.core.deps import require_role
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogOut
from app.schemas.common import PageResponse
from app.middleware.audit import audit_enabled

router = APIRouter(prefix="/audit-logs", tags=["操作日志"])


@router.get("/status")
async def get_status(_=Depends(require_role([0]))):
    return {"enabled": audit_enabled}


@router.put("/toggle")
async def toggle(_=Depends(require_role([0]))):
    import app.middleware.audit as audit_mod
    audit_mod.audit_enabled = not audit_mod.audit_enabled
    return {"enabled": audit_mod.audit_enabled}


@router.get("", response_model=PageResponse[AuditLogOut])
async def list_logs(user_id: int = None, keyword: str = None, role: int = None,
                    date_from: str = None, date_to: str = None,
                    page: int = 1, page_size: int = 10,
                    sort_by: str = None, sort_order: str = None,
                    _=Depends(require_role([0])), db: AsyncSession = Depends(get_db)):
    query = select(AuditLog)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if keyword:
        query = query.where(
            AuditLog.action.contains(keyword) | AuditLog.ip_address.contains(keyword)
        )
    if role is not None:
        query = query.where(AuditLog.role == role)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    if sort_by and sort_by in {'id', 'action', 'created_at'}:
        col = getattr(AuditLog, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        query = query.order_by(col)
    else:
        query = query.order_by(AuditLog.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)
