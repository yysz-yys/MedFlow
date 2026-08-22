from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_role
from app.models.data_dict import DataDict
from app.schemas.data_dict import DataDictCreate, DataDictUpdate, DataDictOut
from app.schemas.common import PageResponse

router = APIRouter(prefix="/data-dict", tags=["数据字典"])


@router.get("", response_model=PageResponse[DataDictOut])
async def list_all(type: str = None, keyword: str = None,
                   page: int = 1, page_size: int = 10,
                   sort_by: str = None, sort_order: str = None,
                   db: AsyncSession = Depends(get_db)):
    base = select(DataDict)
    if type:
        base = base.where(DataDict.dict_type == type)
    if keyword:
        base = base.where(DataDict.dict_label.contains(keyword) | DataDict.dict_type.contains(keyword))
    if sort_by and sort_by in {'id', 'dict_type', 'dict_key', 'sort_order'}:
        col = getattr(DataDict, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        base = base.order_by(col)
    else:
        base = base.order_by(DataDict.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    items = (await db.execute(base.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("")
async def create(
    req: DataDictCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    existing = (
        await db.execute(
            select(DataDict).where(
                DataDict.dict_type == req.dict_type, DataDict.dict_key == req.dict_key
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="该字典条目已存在")
    d = DataDict(**req.model_dump())
    db.add(d)
    await db.flush()
    return {"id": d.id, "dict_type": d.dict_type, "dict_key": d.dict_key}


@router.put("/{dict_id}")
async def update(
    dict_id: int,
    req: DataDictUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    d = (
        await db.execute(select(DataDict).where(DataDict.id == dict_id))
    ).scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    return {"message": "更新成功"}


@router.delete("/{dict_id}")
async def remove(
    dict_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    d = (
        await db.execute(select(DataDict).where(DataDict.id == dict_id))
    ).scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404)
    await db.delete(d)
    return {"message": "已删除"}
