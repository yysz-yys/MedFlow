from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, literal_column, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserListOut, UserStatusUpdate, ResetPasswordRequest, UserResetRequest
from app.schemas.common import PageResponse
from app.services.auth_service import verify_code

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=PageResponse[UserListOut])
async def list_users(
    role: int = None, status: int = None, keyword: str = None,
    page: int = 1, page_size: int = 20,
    sort_by: str = None, sort_order: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_role([0])),
):
    query = select(User)
    if role is not None:
        query = query.where(User.role == role)
    if status is not None:
        query = query.where(User.status == status)
    if keyword:
        query = query.where(User.name.contains(keyword) | User.email.contains(keyword))
    # 当前登录管理员始终排在第一位
    query = query.order_by(case((User.id == current_user.id, 0), else_=1))
    if sort_by and sort_by in {'id', 'name', 'email', 'phone', 'role', 'status', 'created_at'}:
        if sort_by == 'name':
            col = literal_column("CONVERT(`user`.`name` USING gbk)")
        else:
            col = getattr(User, sort_by)
        query = query.order_by(col.desc()) if sort_order == 'desc' else query.order_by(col.asc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=UserListOut)
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    existing = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    user = User(email=req.email, password=hash_password(req.password), name=req.name, role=req.role, phone=req.phone)
    db.add(user)
    await db.flush()
    return user


@router.get("/{user_id}", response_model=UserListOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    req: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.name is not None:
        user.name = req.name
    if req.phone is not None:
        user.phone = req.phone
    if req.role is not None:
        user.role = req.role
    return {"message": "更新成功"}


@router.put("/{user_id}/status")
async def update_status(
    user_id: int,
    req: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = req.status
    if req.status == 1 and user.role in (1, 2):
        from app.models.doctor import Doctor
        from app.models.patient import Patient
        if user.role == 1:
            dr = (await db.execute(select(Doctor).where(Doctor.user_id == user.id, Doctor.deleted_at.isnot(None)))).scalar_one_or_none()
            if dr:
                dr.deleted_at = None
        elif user.role == 2:
            pt = (await db.execute(select(Patient).where(Patient.user_id == user.id, Patient.deleted_at.isnot(None)))).scalar_one_or_none()
            if pt:
                pt.deleted_at = None
    return {"message": "更新成功"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.new_password:
        user.password = hash_password(req.new_password)
    if req.email:
        existing = (await db.execute(select(User).where(User.email == req.email, User.id != user_id))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="该邮箱已被使用")
        user.email = req.email
    return {"message": "已保存"}


@router.post("/{user_id}/reset")
async def reset_user(
    user_id: int,
    req: UserResetRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role([0])),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证验证码
    ok = await verify_code(db, user.email, req.code, "RESET")
    if not ok:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    if req.new_email is not None:
        existing = (await db.execute(select(User).where(User.email == req.new_email, User.id != user_id))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="该邮箱已被使用")
        user.email = req.new_email
    if req.new_password is not None:
        user.password = hash_password(req.new_password)

    return {"message": "已保存"}
