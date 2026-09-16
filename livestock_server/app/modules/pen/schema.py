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
    species: Optional[str] = None
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
    species: Optional[str] = Field(None, description="所属畜种：牛/羊/猪；不传则视为待归属")
    capacity: int = Field(..., ge=1, description="容纳上限")
    remark: Optional[str] = Field(None, max_length=200)


class PenUpdateIn(BaseModel):
    """修改圈舍"""
    pen_code: Optional[str] = None
    pen_type: Optional[str] = None
    species: Optional[str] = Field(None, description="所属畜种：牛/羊/猪；空串表示清除归属")
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
