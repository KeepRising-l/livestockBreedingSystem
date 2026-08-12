"""
认证相关 schemas
"""
from typing import Optional

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    """登录请求"""
    username: str = Field(..., description="账号")
    password: str = Field(..., description="密码")


class OwnerRegisterIn(BaseModel):
    """养殖场主注册"""
    farm_name: str = Field(..., max_length=100, description="养殖场名称")
    username: str = Field(..., max_length=50, description="登录账号")
    password: str = Field(..., min_length=6, description="密码")
    real_name: str = Field(..., max_length=50, description="姓名")
    phone: str = Field(..., max_length=20, description="手机号")
    livestock_types: str = Field(..., description="养殖种类，逗号分隔：牛,羊,猪")


class EmployeeRegisterIn(BaseModel):
    """员工注册"""
    farm_id: Optional[int] = Field(None, description="就职养殖场ID（可选，默认从当前用户/X-Farm-Id 头取）")
    username: str = Field(..., max_length=50, description="登录账号")
    password: str = Field(..., min_length=6, description="密码")
    real_name: str = Field(..., max_length=50, description="姓名")
    phone: str = Field(..., max_length=20, description="手机号")
    post: str = Field(..., description="岗位：饲喂员/兽医/繁育员/库管员")
