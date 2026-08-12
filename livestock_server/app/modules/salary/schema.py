"""
薪资配置 DTO

- SalaryConfigIn：新增（岗位必填 + 基础薪资必填）
- SalaryConfigUpdateIn：修改（不含 post，岗位作为唯一 key 不可改）
- SalaryConfigOut：返回
- SalaryConfigQuery：列表查询（按岗位/状态筛选 + 分页）
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SalaryConfigIn(BaseModel):
    """新增薪资配置"""
    post: str = Field(..., max_length=20, description="岗位：饲喂员/兽医/繁育员/库管员")
    base_salary: float = Field(..., gt=0, description="基础薪资")
    bonus_ratio: Optional[float] = Field(None, ge=0, le=100, description="奖金比例（%）")
    deduct_rule: Optional[str] = Field(None, max_length=255, description="扣罚规则")
    status: int = Field(1, description="状态：1启用 0停用")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class SalaryConfigUpdateIn(BaseModel):
    """修改薪资配置（岗位不可改）"""
    base_salary: Optional[float] = Field(None, gt=0, description="基础薪资")
    bonus_ratio: Optional[float] = Field(None, ge=0, le=100, description="奖金比例（%）")
    deduct_rule: Optional[str] = Field(None, max_length=255, description="扣罚规则")
    status: Optional[int] = Field(None, description="状态：1启用 0停用")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class SalaryConfigOut(BaseModel):
    """薪资配置返回"""
    id: int
    farm_id: int
    post: str
    base_salary: float
    bonus_ratio: Optional[float] = None
    deduct_rule: Optional[str] = None
    status: int
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class SalaryConfigQuery(BaseModel):
    """薪资配置列表查询"""
    post: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 10
