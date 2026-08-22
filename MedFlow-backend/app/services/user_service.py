from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import hash_password


async def get_users(
    db: AsyncSession, role: int = None, status: int = None,
    keyword: str = None, page: int = 1, page_size: int = 20,
):
    from sqlalchemy import func
    query = select(User)
    if role is not None:
        query = query.where(User.role == role)
    if status is not None:
        query = query.where(User.status == status)
    if keyword:
        query = query.where(User.name.contains(keyword) | User.email.contains(keyword))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(
        query.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "items": items}


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


async def set_user_status(db: AsyncSession, user_id: int, status: int):
    user = await get_user_by_id(db, user_id)
    user.status = status
    return user


async def reset_user_password(db: AsyncSession, user_id: int, new_password: str):
    user = await get_user_by_id(db, user_id)
    user.password = hash_password(new_password)
    return user
