"""
异常处理模块

定义业务异常类，并通过 FastAPI 异常处理器统一捕获返回 Result 格式。
这样业务代码里直接 `raise BizException("耳标已存在")` 即可，不用层层 try/except。
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import Result


class BizException(Exception):
    """业务异常：在业务逻辑中主动抛出"""

    def __init__(self, msg: str = "业务异常", code: int = 500):
        self.msg = msg
        self.code = code
        super().__init__(msg)


async def biz_exception_handler(request: Request, exc: BizException):
    """业务异常统一处理"""
    return JSONResponse(
        status_code=200,  # HTTP 仍返回 200，靠 code 字段区分
        content=Result.fail(msg=exc.msg, code=exc.code).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验异常处理"""
    # 取第一条错误信息，便于前端展示
    errors = exc.errors()
    msg = "参数校验失败"
    if errors:
        first = errors[0]
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = f"{loc}: {first.get('msg', '校验失败')}"
    return JSONResponse(
        status_code=200,
        content=Result.fail(msg=msg, code=400).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception):
    """兜底异常处理，防止堆栈信息泄露给前端"""
    return JSONResponse(
        status_code=200,
        content=Result.fail(msg="服务器内部错误", code=500).model_dump(),
    )
