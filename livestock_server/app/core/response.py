"""
统一响应格式

所有接口都返回这个结构：
{
    "code": 200,           # 业务码，200 表示成功，其它表示业务错误
    "msg": "success",      # 提示信息
    "data": {...},         # 业务数据，无数据时为 null
    "timestamp": 1234567890
}
"""
from typing import Any, Optional, Generic, TypeVar, List
from datetime import datetime

from pydantic import BaseModel, Field

# 泛型类型变量，让 Result 可以承载任意类型的数据
T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """统一返回结果"""

    code: int = 200
    msg: str = "success"
    data: Optional[T] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

    @classmethod
    def ok(cls, data: Any = None, msg: str = "success") -> "Result":
        """成功返回"""
        return cls(code=200, msg=msg, data=data)

    @classmethod
    def fail(cls, msg: str = "fail", code: int = 500, data: Any = None) -> "Result":
        """失败返回"""
        return cls(code=code, msg=msg, data=data)


class PageResult(BaseModel, Generic[T]):
    """分页返回结果"""

    list: List[T] = Field(default_factory=list)
    total: int = 0
    pageNum: int = 1
    pageSize: int = 10

    @classmethod
    def of(cls, items: list, total: int, pageNum: int, pageSize: int) -> "PageResult":
        return cls(list=items, total=total, pageNum=pageNum, pageSize=pageSize)
