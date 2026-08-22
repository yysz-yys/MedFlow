from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.models.drug import Drug
from app.schemas.drug import DrugCreate, DrugUpdate, DrugStockUpdate, DrugOut
from app.schemas.common import PageResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/drugs", tags=["药品"])

@router.get("", response_model=PageResponse[DrugOut])
async def list_drugs(page: int = 1, page_size: int = 10, keyword: str = None,
                     status: int = None, unit: str = None,
                     stock_lte: int = None,
                     sort_by: str = None, sort_order: str = None,
                     db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    base = select(Drug)
    if keyword:
        base = base.where(Drug.name.contains(keyword) | Drug.manufacturer.contains(keyword))
    if status == 0:
        base = base.where(Drug.deleted_at.is_(None))
    elif status == 1:
        base = base.where(Drug.deleted_at.isnot(None))
    if unit:
        base = base.where(Drug.unit == unit)
    if stock_lte is not None:
        base = base.where(Drug.stock <= stock_lte)
    if sort_by and sort_by in {'id', 'name', 'price', 'stock', 'created_at', 'deleted_at'}:
        if sort_by == 'name':
            col = literal_column("CONVERT(`drug`.`name` USING gbk)")
        else:
            col = getattr(Drug, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        base = base.order_by(col)
    else:
        base = base.order_by(Drug.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    items = (await db.execute(base.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)

@router.post("")
async def create(req: DrugCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    drug = Drug(**req.model_dump())
    db.add(drug)
    await db.flush()
    return {"id": drug.id, "name": drug.name}

@router.put("/{drug_id}")
async def update(drug_id: int, req: DrugUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Drug).where(Drug.id == drug_id, Drug.deleted_at.is_(None)))
    drug = result.scalar_one_or_none()
    if drug is None: raise HTTPException(status_code=404)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(drug, k, v)
    return {"message": "更新成功"}

@router.delete("/{drug_id}")
async def soft_delete(drug_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Drug).where(Drug.id == drug_id, Drug.deleted_at.is_(None)))
    drug = result.scalar_one_or_none()
    if drug is None: raise HTTPException(status_code=404)
    drug.deleted_at = datetime.now(timezone.utc)
    return {"message": "已删除"}

@router.put("/{drug_id}/restore")
async def restore(drug_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Drug).where(Drug.id == drug_id, Drug.deleted_at.isnot(None)))
    drug = result.scalar_one_or_none()
    if drug is None: raise HTTPException(status_code=404, detail="药品不存在或未被删除")
    drug.deleted_at = None
    return {"message": "已恢复"}

@router.put("/{drug_id}/stock")
async def adjust_stock(drug_id: int, req: DrugStockUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Drug).where(Drug.id == drug_id, Drug.deleted_at.is_(None)))
    drug = result.scalar_one_or_none()
    if drug is None: raise HTTPException(status_code=404)
    new_stock = drug.stock + req.change
    if new_stock < 0: raise HTTPException(status_code=400, detail="库存不足")
    drug.stock = new_stock
    return {"message": "库存已更新", "stock": drug.stock}
