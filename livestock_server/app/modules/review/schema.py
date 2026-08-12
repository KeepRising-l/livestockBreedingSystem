"""
审核 DTO

统一审核入口，不新增业务表，跨模块读取各业务表的待审核记录。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewItemOut(BaseModel):
    """通用待审核项返回（各业务类型统一结构）"""
    business_type: str
    business_name: str
    id: int
    create_time: Optional[datetime] = None
    operator_user_id: Optional[int] = None
    operator_name: Optional[str] = None
    summary: str
    detail: dict = {}


class ReviewAuditIn(BaseModel):
    """统一审核动作"""
    business_type: str = Field(..., description="业务类型：feeding/purchase/consume/vaccine/medical")
    business_id: int = Field(..., description="业务记录ID")
    audit_status: str = Field(..., description="目标审核状态：通过/驳回")
    remark: Optional[str] = Field(None, max_length=255, description="审核备注")


class ReviewCountsOut(BaseModel):
    """各类型待审核数量"""
    feeding: int = 0
    purchase: int = 0
    consume: int = 0
    vaccine: int = 0
    medical: int = 0
    total: int = 0
