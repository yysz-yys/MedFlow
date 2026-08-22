from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: list[T]

    class Config:
        from_attributes = True


class BaseResponse(BaseModel):
    code: int = 0
    message: str = "ok"
