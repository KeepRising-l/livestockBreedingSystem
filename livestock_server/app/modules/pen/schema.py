"""
圈舍 DTO
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PenOut(BaseModel):
    """圈舍信息返回"""
    id: int
    farm_id: int
    pen_code: str
    pen_type: str
    capacity: int
    current_count: int
    status: int
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class PenAddIn(BaseModel):
    """新增圈舍"""
    pen_code: str = Field(..., max_length=20, description="圈舍编号")
    pen_type: str = Field(..., description="圈舍类型：A/B/C/D")
    capacity: int = Field(..., ge=1, description="容纳上限")
    remark: Optional[str] = Field(None, max_length=200)


class PenUpdateIn(BaseModel):
    """修改圈舍"""
    pen_code: Optional[str] = None
    pen_type: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class PenQuery(BaseModel):
    """圈舍列表查询"""
    pen_type: Optional[str] = None
    species: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 10
