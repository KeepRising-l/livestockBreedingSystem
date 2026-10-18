"""
圈舍 DTO
"""
from datetime import datetime
from typing import List, Optional

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
    pen_code: str = Field(..., max_length=20, description="圈舍编号，在本畜种内唯一（如 A01）")
    pen_type: str = Field(..., description="圈舍类型：A/B/C/D")
    species: Optional[str] = Field(None, description="所属畜种：牛/羊/猪；不传则视为待归属")
    capacity: int = Field(..., ge=1, description="容纳上限")
    remark: Optional[str] = Field(None, max_length=200)


class PenBatchAddIn(BaseModel):
    """批量添加圈舍

    编号有两种给法，codes 优先：
    - codes：直接给编号列表（前端预览后允许用户手工编辑）
    - prefix + start_no + count：由服务端按「前缀 + 起始序号」生成，序号补 2 位（A + 1 + 12 -> A01~A12）
    """
    species: Optional[str] = Field(None, description="所属畜种：牛/羊/猪；不传则视为待归属")
    pen_type: str = Field(..., description="圈舍类型：A/B/C/D")
    capacity: int = Field(..., description="容纳上限，必须大于 0")
    remark: Optional[str] = Field(None, max_length=200)
    codes: Optional[List[str]] = Field(
        None, description="圈舍编号列表（优先使用），单次最多 50 条"
    )
    prefix: Optional[str] = Field(None, description="编号前缀（字母，如 A），与起始序号、数量配合生成编号")
    start_no: Optional[int] = Field(None, description="起始序号，如 1")
    count: Optional[int] = Field(None, description="生成数量，最多 50 条")


class PenBatchSkipOut(BaseModel):
    """批量添加中被跳过的编号及原因"""
    code: str
    reason: str


class PenBatchAddOut(BaseModel):
    """批量添加结果"""
    created: int = 0
    created_codes: List[str] = Field(default_factory=list)
    skipped: List[PenBatchSkipOut] = Field(default_factory=list)


class PenUpdateIn(BaseModel):
    """修改圈舍"""
    pen_code: Optional[str] = Field(None, description="圈舍编号，在本畜种内唯一")
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
