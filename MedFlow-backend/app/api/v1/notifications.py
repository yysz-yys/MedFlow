from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db; from app.core.deps import get_current_user, require_role
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationAdminItem, NotificationOut, NotificationCreate
from app.schemas.common import PageResponse

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=PageResponse[NotificationOut])
async def list_notifications(page: int = 1, page_size: int = 20,
                              type: str | None = None,
                              current_user=Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    base = select(Notification).where(Notification.user_id == current_user.id)
    if type:
        if type == 'SYSTEM':
            base = base.where(Notification.type.in_(['SYSTEM', 'SYSTEM_IMPORTANT']))
        else:
            base = base.where(Notification.type == type)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    items = (await db.execute(base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/unread-count")
async def unread_count(current_user=Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    count = (await db.execute(select(func.count()).select_from(Notification).where(
        Notification.user_id == current_user.id, Notification.is_read == 0))).scalar()
    return {"unread_count": count}


@router.post("")
async def create_notification(req: NotificationCreate,
                               _=Depends(require_role([0])),
                               db: AsyncSession = Depends(get_db)):
    if req.user_id:
        db.add(Notification(user_id=req.user_id, title=req.title, content=req.content, type=req.type))
        count = 1
    else:
        users = (await db.execute(select(User.id))).scalars().all()
        for uid in users:
            db.add(Notification(user_id=uid, title=req.title, content=req.content, type=req.type))
        count = len(users)
    await db.flush()
    return {"message": "通知已发送", "recipients": count}


@router.put("/{notification_id}/read")
async def mark_read(notification_id: int, current_user=Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    n = (await db.execute(select(Notification).where(
        Notification.id == notification_id, Notification.user_id == current_user.id
    ))).scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=404, detail="通知不存在")
    n.is_read = 1
    return {"message": "已标记已读"}


@router.get("/admin", response_model=PageResponse[NotificationAdminItem])
async def admin_list_notifications(
    page: int = 1,
    page_size: int = 20,
    title: str | None = None,
    type: str | None = None,
    current_user=Depends(get_current_user),
    _=Depends(require_role([0])),
    db: AsyncSession = Depends(get_db),
):
    """管理员查看发送历史（去重，按 title+content+type 分组）"""
    sub = (
        select(
            func.min(Notification.id).label("id"),
            Notification.title,
            Notification.content,
            Notification.type,
            func.count().label("recipient_count"),
            func.min(Notification.created_at).label("created_at"),
        )
        .select_from(Notification)
    )

    conditions = []
    if title:
        conditions.append(Notification.title.contains(title))
    if type:
        conditions.append(Notification.type == type)
    if conditions:
        sub = sub.where(and_(*conditions))

    sub = sub.group_by(
        Notification.title, Notification.content, Notification.type
    ).subquery()

    count_q = select(func.count()).select_from(sub)
    total = (await db.execute(count_q)).scalar()

    items_q = (
        select(sub)
        .order_by(sub.c.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(items_q)).all()

    items = [
        NotificationAdminItem(
            id=row.id,
            title=row.title,
            content=row.content,
            type=row.type,
            recipient_count=row.recipient_count,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return PageResponse(total=total, page=page, page_size=page_size, items=items)
