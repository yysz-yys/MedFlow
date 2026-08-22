import aiosmtplib
from email.mime.text import MIMEText
from app.core.config import get_settings

settings = get_settings()


async def send_verification_code(to_email: str, code: str) -> None:
    subject = "云诊易 MedFlow — 验证码"
    body = f"您的验证码是：{code}，{settings.CODE_EXPIRE_MINUTES} 分钟内有效。请勿泄露给他人。"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=True,
    )
