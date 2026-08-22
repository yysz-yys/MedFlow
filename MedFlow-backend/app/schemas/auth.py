from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SendCodeRequest(BaseModel):
    email: EmailStr
    scene: str = Field(..., pattern="^(REGISTER|LOGIN|RESET_PASSWORD|RESET)$")
    captcha_id: str = ""
    captcha_text: str = ""


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=6, max_length=6)
    role: int = Field(..., ge=1, le=2)  # 1=医生 / 2=病人


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = ""
    code: Optional[str] = None
    captcha_id: str = ""
    captcha_text: str = ""


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: int
    status: int

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=50)

class ResetPasswordByCodeRequest(BaseModel):
    email: str = Field(..., max_length=255)
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=50)
