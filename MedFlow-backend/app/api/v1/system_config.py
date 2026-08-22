from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.models.system_config import SystemConfig
from app.schemas.system_config import ConfigCreate, ConfigUpdate, ConfigOut
from app.schemas.common import PageResponse

router = APIRouter(prefix="/system-config", tags=["系统配置"])


@router.get("", response_model=PageResponse[ConfigOut])
async def list_all(page: int = 1, page_size: int = 10, keyword: str = None,
                   sort_by: str = None, sort_order: str = None,
                   db: AsyncSession = Depends(get_db)):
    base = select(SystemConfig)
    if keyword:
        base = base.where(SystemConfig.config_key.contains(keyword) | SystemConfig.description.contains(keyword))
    if sort_by and sort_by in {'id', 'config_key', 'created_at'}:
        col = getattr(SystemConfig, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        base = base.order_by(col)
    else:
        base = base.order_by(SystemConfig.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    items = (await db.execute(base.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/by-key", response_model=ConfigOut)
async def get_by_key(
    key: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """按 config_key 获取单条配置"""
    c = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == key)
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="配置不存在")
    return c


@router.post("", response_model=ConfigOut)
async def create(
    req: ConfigCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    existing = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == req.config_key)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="配置键已存在")
    c = SystemConfig(**req.model_dump())
    db.add(c)
    await db.flush()
    return c


@router.put("/{config_id}")
async def update(
    config_id: int,
    req: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    c = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.id == config_id)
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="配置不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    return {"message": "更新成功"}


@router.delete("/{config_id}")
async def remove(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    c = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.id == config_id)
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="配置不存在")
    await db.delete(c)
    return {"message": "已删除"}
