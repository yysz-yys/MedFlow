from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request


class AppException(HTTPException):
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})


async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"code": 500, "message": "服务器内部错误"})
