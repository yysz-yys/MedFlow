import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import get_settings
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.verification_code import VerificationCode
from app.utils.email import send_verification_code

settings = get_settings()


async def send_code(db: AsyncSession, email: str, scene: str, ip: str) -> None:
    # 频率检查（同一邮箱+场景+IP在间隔内只发一条）
    interval_ago = datetime.now(timezone.utc) - timedelta(seconds=settings.CODE_SEND_INTERVAL_SEC)
    result = await db.execute(
        select(func.count()).select_from(VerificationCode)
        .where(
            VerificationCode.target == email,
            VerificationCode.scene == scene,
            VerificationCode.send_ip == ip,
            VerificationCode.created_at > interval_ago,
        )
    )
    if result.scalar() >= 1:
        raise HTTPException(status_code=429, detail="发送过于频繁，请60秒后再试")

    import random
    code = "".join([str(random.randint(0, 9)) for _ in range(settings.CODE_LENGTH)])

    vc = VerificationCode(
        target=email, code=code, scene=scene, send_ip=ip,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.CODE_EXPIRE_MINUTES),
    )
    db.add(vc)

    try:
        await send_verification_code(email, code)
    except Exception:
        raise HTTPException(status_code=500, detail="邮件发送失败，请稍后重试")


async def verify_code(db: AsyncSession, email: str, code: str, scene: str) -> bool:
    now = datetime.now(timezone.utc)

    # 查找该邮箱 + 场景下最新一条未使用未过期的验证码
    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.target == email,
            VerificationCode.scene == scene,
            VerificationCode.expires_at > now,
            VerificationCode.used == 0,
        ).order_by(VerificationCode.created_at.desc()).limit(1)
    )
    vc = result.scalar_one_or_none()
    if vc is None:
        return False

    # 检查重试次数
    if vc.attempt_count >= settings.CODE_MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail="验证码已失效（重试次数过多）")

    # code 不匹配 → 递增计数
    if vc.code != code:
        vc.attempt_count += 1
        await db.flush()
        return False

    # 匹配成功 → 标记已使用
    vc.used = 1
    await db.flush()
    return True


async def register(db: AsyncSession, data) -> dict:
    # 校验邮箱唯一
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    user = User(
        email=data.email, password=hash_password(data.password),
        name=data.name, role=data.role,
    )
    db.add(user)
    await db.flush()

    if data.role == 1:  # 医生：只创建 User，Doctor 档案由管理员通过 POST /doctors 创建
        pass
    elif data.role == 2:  # 病人
        patient = Patient(user_id=user.id)
        db.add(patient)

    return {"message": "注册成功", "user_id": user.id}


async def login(db: AsyncSession, data) -> dict:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    if user.status == 0:
        raise HTTPException(status_code=401, detail="账户已被禁用，请联系管理员")

    if data.code:
        await verify_code(db, data.email, data.code, "LOGIN")
    else:
        if not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = create_access_token({"sub": str(user.id), "jti": uuid.uuid4().hex})
    return {"access_token": token, "user": user}


async def logout(db: AsyncSession, user: User, jti: str) -> None:
    from app.models.token_blacklist import TokenBlacklist
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    tb = TokenBlacklist(token_jti=jti, user_id=user.id, expires_at=expire)
    db.add(tb)
