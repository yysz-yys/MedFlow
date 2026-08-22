from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from .auth import UserOut


class UserListOut(UserOut):
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    status: int = Field(..., ge=0, le=1)


class ResetPasswordRequest(BaseModel):
    new_password: Optional[str] = Field(None, min_length=6, max_length=50)
    email: Optional[str] = Field(None, max_length=100)


class UserCreate(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    name: str = Field(..., max_length=50)
    role: int = Field(..., ge=0, le=2)
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = None
    role: Optional[int] = Field(None, ge=0, le=2)


class UserResetRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    new_email: Optional[str] = Field(None, max_length=100)
    new_password: Optional[str] = Field(None, min_length=6, max_length=50)
