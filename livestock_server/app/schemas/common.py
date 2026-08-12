"""
通用 schemas：分页请求、token 返回等
"""
from typing import Optional

from pydantic import BaseModel, Field


class PageQuery(BaseModel):
    """分页查询基础参数，其它查询 schema 继承它"""
    pageNum: int = Field(1, ge=1, description="页码，从1开始")
    pageSize: int = Field(10, ge=1, le=100, description="每页条数")


class TokenOut(BaseModel):
    """登录成功返回的 token"""
    access_token: str
    token_type: str = "bearer"
