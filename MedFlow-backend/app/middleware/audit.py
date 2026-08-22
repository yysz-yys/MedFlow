from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import async_session
from app.models.audit_log import AuditLog
from app.models.user import User
from sqlalchemy import select

# 操作日志开关
audit_enabled = True

# 需要记录的 method + path 前缀
LOG_RULES = {
    "POST": {
        "/api/v1/auth/login": {"action": "LOGIN", "target_type": "user"},
        "/api/v1/auth/logout": {"action": "LOGOUT", "target_type": "user"},
        "/api/v1/auth/register": {"action": "REGISTER", "target_type": "user"},
        "/api/v1/users": {"action": "CREATE_USER", "target_type": "user"},
        "/api/v1/departments": {"action": "CREATE_DEPARTMENT", "target_type": "department"},
        "/api/v1/doctors": {"action": "CREATE_DOCTOR", "target_type": "doctor"},
        "/api/v1/patients": {"action": "CREATE_PATIENT", "target_type": "patient"},
        "/api/v1/drugs": {"action": "CREATE_DRUG", "target_type": "drug"},
        "/api/v1/doctor-schedules": {"action": "CREATE_SCHEDULE", "target_type": "doctor_schedule"},
        "/api/v1/appointments": {"action": "CREATE_APPOINTMENT", "target_type": "appointment"},
        "/api/v1/diagnosis-records": {"action": "CREATE_DIAGNOSIS", "target_type": "diagnosis_record"},
        "/api/v1/prescriptions": {"action": "CREATE_PRESCRIPTION", "target_type": "prescription"},
        "/api/v1/drug-orders": {"action": "CREATE_ORDER", "target_type": "drug_order"},
        "/api/v1/notifications": {"action": "SEND_NOTIFICATION", "target_type": "notification"},
        "/api/v1/system-config": {"action": "CREATE_CONFIG", "target_type": "system_config"},
        "/api/v1/data-dict": {"action": "CREATE_DICT", "target_type": "data_dict"},
        "/api/v1/files/upload": {"action": "UPLOAD_FILE", "target_type": "file"},
    },
    "PUT": {
        "/api/v1/users": {"action": "UPDATE_USER", "target_type": "user"},
        "/api/v1/departments": {"action": "UPDATE_DEPARTMENT", "target_type": "department"},
        "/api/v1/doctors": {"action": "UPDATE_DOCTOR", "target_type": "doctor"},
        "/api/v1/patients": {"action": "UPDATE_PATIENT", "target_type": "patient"},
        "/api/v1/drugs": {"action": "UPDATE_DRUG", "target_type": "drug"},
        "/api/v1/doctor-schedules": {"action": "UPDATE_SCHEDULE", "target_type": "doctor_schedule"},
        "/api/v1/appointments": {"action": "UPDATE_APPOINTMENT", "target_type": "appointment"},
        "/api/v1/diagnosis-records": {"action": "UPDATE_DIAGNOSIS", "target_type": "diagnosis_record"},
        "/api/v1/prescriptions": {"action": "UPDATE_PRESCRIPTION", "target_type": "prescription"},
        "/api/v1/drug-orders": {"action": "UPDATE_ORDER", "target_type": "drug_order"},
        "/api/v1/notifications": {"action": "MARK_READ", "target_type": "notification"},
        "/api/v1/system-config": {"action": "UPDATE_CONFIG", "target_type": "system_config"},
        "/api/v1/data-dict": {"action": "UPDATE_DICT", "target_type": "data_dict"},
    },
    "DELETE": {
        "/api/v1/users": {"action": "DELETE_USER", "target_type": "user"},
        "/api/v1/departments": {"action": "DELETE_DEPARTMENT", "target_type": "department"},
        "/api/v1/doctors": {"action": "DELETE_DOCTOR", "target_type": "doctor"},
        "/api/v1/patients": {"action": "DELETE_PATIENT", "target_type": "patient"},
        "/api/v1/drugs": {"action": "DELETE_DRUG", "target_type": "drug"},
        "/api/v1/doctor-schedules": {"action": "DELETE_SCHEDULE", "target_type": "doctor_schedule"},
        "/api/v1/drug-orders": {"action": "DELETE_ORDER", "target_type": "drug_order"},
        "/api/v1/system-config": {"action": "DELETE_CONFIG", "target_type": "system_config"},
        "/api/v1/data-dict": {"action": "DELETE_DICT", "target_type": "data_dict"},
        "/api/v1/files": {"action": "DELETE_FILE", "target_type": "file"},
    },
}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        user_id = getattr(request.state, "user_id", None)
        if user_id is None or not audit_enabled:
            return response

        method = request.method
        path = request.url.path

        # 匹配需要记录的路由
        matched = None
        for prefix, rule in LOG_RULES.get(method, {}).items():
            if path.startswith(prefix):
                matched = rule
                break

        if not matched:
            return response

        if response.status_code >= 400:
            return response

        # 从 URL 中提取目标 ID，如 /api/v1/drugs/123 → 123
        target_id = None
        detail = f"{method} {path}"
        parts = path.rstrip("/").split("/")
        if parts[-1].isdigit():
            target_id = int(parts[-1])

        try:
            async with async_session() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    log = AuditLog(
                        user_id=user.id, user_name=user.name, role=user.role,
                        action=matched["action"], target_type=matched["target_type"],
                        target_id=target_id, detail=detail,
                        ip_address=request.client.host if request.client else None,
                    )
                    db.add(log)
                    await db.commit()
        except Exception:
            pass

        return response
