import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select
from app.core.security import decode_access_token
from app.core.database import async_session
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # OPTIONS 预检请求直接放行
        if request.method == "OPTIONS":
            return await call_next(request)

        # 公开路由跳过认证
        path = request.url.path
        if path == "/" or path.startswith("/docs") or path.startswith("/openapi.json") \
           or path.startswith("/api/v1/auth/register") or path.startswith("/api/v1/auth/send-code") \
           or path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/captcha") \
           or path.startswith("/api/v1/data-dict") or path.startswith("/api/v1/system-config"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "未提供有效令牌"})

        token = auth_header[7:]
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            jti = payload.get("jti", "")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=401, content={"detail": f"令牌无效: {str(e)}"})

        # 检查 token 是否在黑名单中
        async with async_session() as db:
            result = await db.execute(
                select(TokenBlacklist).where(TokenBlacklist.token_jti == jti)
            )
            if result.scalar_one_or_none():
                return JSONResponse(status_code=401, content={"detail": "令牌已失效（已登出）"})

            # 检查用户是否存在且正常
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                return JSONResponse(status_code=401, content={"detail": "用户不存在"})
            if user.status == 0:
                return JSONResponse(status_code=401, content={"detail": "账户已被禁用，请联系管理员"})

        # 将 user_id 存入 request.state 供后续使用
        request.state.user_id = user_id
        request.state.jti = jti

        return await call_next(request)
