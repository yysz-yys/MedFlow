from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.schemas.common import PageResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/departments", tags=["科室"])

@router.get("", response_model=PageResponse[DepartmentOut])
async def list_all(page: int = 1, page_size: int = 10, keyword: str = None,
                   sort_by: str = None, sort_order: str = None,
                   db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    base = select(Department)
    if keyword:
        base = base.where(Department.name.contains(keyword) | Department.description.contains(keyword))
    if sort_by and sort_by in {'id', 'name', 'created_at', 'deleted_at'}:
        if sort_by == 'name':
            col = literal_column("CONVERT(`department`.`name` USING gbk)")
        else:
            col = getattr(Department, sort_by)
        if sort_order == 'desc':
            col = col.desc()
        base = base.order_by(col)
    elif keyword:
        base = base.order_by(case((Department.name.contains(keyword), 0), else_=1), Department.id)
    else:
        base = base.order_by(Department.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    items = (await db.execute(base.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)

@router.post("")
async def create(req: DepartmentCreate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    dept = Department(name=req.name, description=req.description)
    db.add(dept)
    await db.flush()
    return {"id": dept.id, "name": dept.name, "description": dept.description}

@router.put("/{dept_id}")
async def update(dept_id: int, req: DepartmentUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Department).where(Department.id == dept_id, Department.deleted_at.is_(None)))
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=404, detail="科室不存在")
    if req.name is not None: dept.name = req.name
    if req.description is not None: dept.description = req.description
    return {"message": "更新成功"}

@router.delete("/{dept_id}")
async def soft_delete(dept_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Department).where(Department.id == dept_id, Department.deleted_at.is_(None)))
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=404, detail="科室不存在")
    dept.deleted_at = datetime.now(timezone.utc)
    return {"message": "已删除"}

@router.put("/{dept_id}/restore")
async def restore(dept_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_role([0]))):
    result = await db.execute(select(Department).where(Department.id == dept_id, Department.deleted_at.isnot(None)))
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=404, detail="科室不存在或未被删除")
    dept.deleted_at = None
    return {"message": "已恢复"}
