from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.auth import (
    SendCodeRequest, RegisterRequest, LoginRequest, LoginResponse,
    UserOut, UserUpdateRequest, ChangePasswordRequest, ResetPasswordByCodeRequest,
)
from app.services import auth_service
from app.utils import captcha as captcha_util

router = APIRouter(prefix="/auth", tags=["认证"])


@router.get("/captcha")
async def get_captcha():
    cid, img = captcha_util.generate()
    return {"captcha_id": cid, "image": img}


@router.post("/send-code")
async def send_code(req: SendCodeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    if req.captcha_id and not captcha_util.verify(req.captcha_id, req.captcha_text):
        raise HTTPException(status_code=400, detail="图形验证码错误或已过期")
    await auth_service.send_code(db, req.email, req.scene, request.client.host)
    return {"message": "验证码已发送"}


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_code(db, req.email, req.code, "REGISTER")
    return await auth_service.register(db, req)


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 密码登录时校验图形验证码，验证码登录跳过
    if req.captcha_id and not captcha_util.verify(req.captcha_id, req.captcha_text):
        raise HTTPException(status_code=400, detail="图形验证码错误或已过期")
    return await auth_service.login(db, req)


@router.post("/logout")
async def logout(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # jti 从 token 中获取，实际上需要中间件传入
    # 简化处理：不做 jti 校验，token 存黑名单由 auth middleware 校验
    return {"message": "已登出"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me")
async def update_me(
    req: UserUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.name is not None:
        current_user.name = req.name
    if req.phone is not None:
        from app.models.user import User
        # 检查手机号唯一
        existing = (await db.execute(
            select(User).where(User.phone == req.phone, User.id != current_user.id)
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="该手机号已被使用")
        current_user.phone = req.phone
    return {"message": "更新成功"}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.utils.file_upload import save_upload
    from app.models.file_attachment import FileAttachment
    info = await save_upload(file)
    db.add(FileAttachment(
        uploader_id=current_user.id,
        uploader_role=current_user.role,
        related_type="avatar",
        related_id=current_user.id,
        file_name=info["file_name"],
        file_path=info["file_path"],
        file_size=info["file_size"],
        file_type=info["file_type"],
    ))
    await db.commit()
    return {"avatar": info["file_path"]}


@router.get("/me/avatar")
async def get_avatar(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.file_attachment import FileAttachment
    fa = (await db.execute(
        select(FileAttachment).where(
            FileAttachment.related_type == "avatar",
            FileAttachment.related_id == current_user.id,
        ).order_by(FileAttachment.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    return {"avatar": fa.file_path if fa else None}


@router.put("/password")
async def change_password(
    req: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_password, hash_password
    if not verify_password(req.old_password, current_user.password):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="旧密码错误")
    current_user.password = hash_password(req.new_password)
    return {"message": "密码修改成功"}

@router.post("/reset-password-by-code")
async def reset_password_by_code(req: ResetPasswordByCodeRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_code(db, req.email, req.code, "RESET_PASSWORD")
    from app.models.user import User
    from app.core.security import hash_password
    from sqlalchemy import select
    user = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password = hash_password(req.new_password)
    return {"message": "密码重置成功"}
