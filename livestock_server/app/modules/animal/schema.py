"""
档案 DTO
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnimalOut(BaseModel):
    """档案信息返回"""
    id: int
    farm_id: int
    ear_tag: str
    species: str
    breed: str
    pen_id: Optional[int] = None
    gender: str
    birth_date: Optional[date] = None
    in_date: Optional[date] = None
    out_date: Optional[date] = None
    growth_stage: Optional[str] = None
    status: str
    source: Optional[str] = None
    sire_tag: Optional[str] = None
    dam_tag: Optional[str] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnimalIndividualIn(BaseModel):
    """个体入栏请求"""
    species: str = Field(..., description="畜种：牛/羊/猪")
    breed: str = Field(..., description="品种")
    gender: str = Field(..., description="性别：公/母")
    birth_date: Optional[date] = None
    in_date: Optional[date] = None
    status: str = "在栏"
    source: Optional[str] = Field(None, description="来源：自繁/外购")
    sire_tag: Optional[str] = None
    dam_tag: Optional[str] = None
    remark: Optional[str] = None
    pen_id: Optional[int] = Field(None, description="指定圈舍ID，不传则自动分配")


class AnimalBatchIn(BaseModel):
    """批量入栏请求"""
    species: str = Field(..., description="畜种")
    breed: str = Field(..., description="品种")
    gender: str = Field(..., description="性别：公/母（批量默认同一性别）")
    count: int = Field(..., ge=1, description="入栏数量")
    birth_date: Optional[date] = None
    in_date: Optional[date] = None
    status: str = "在栏"
    source: Optional[str] = None
    remark: Optional[str] = None


class AnimalQuery(BaseModel):
    """档案列表查询"""
    ear_tag: Optional[str] = None
    pen_id: Optional[int] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10


class BatchDeleteIn(BaseModel):
    """批量删除"""
    ids: list[int] = Field(..., description="档案ID列表")


class AnimalUpdateIn(BaseModel):
    """档案修改（所有字段可选，仅更新传入字段）"""
    breed: Optional[str] = Field(None, description="品种")
    species: Optional[str] = Field(None, description="畜种，变更时重算生长阶段")
    pen_id: Optional[int] = Field(None, description="圈舍ID，变更时重新生成耳标")
    gender: Optional[str] = Field(None, description="性别：公/母")
    birth_date: Optional[date] = Field(None, description="出生日期，变更时重算生长阶段")
    in_date: Optional[date] = Field(None, description="入栏日期")
    status: Optional[str] = Field(None, description="状态")
    source: Optional[str] = Field(None, description="来源")
    sire_tag: Optional[str] = Field(None, description="父本耳标")
    dam_tag: Optional[str] = Field(None, description="母本耳标")
    remark: Optional[str] = Field(None, description="备注")


class AnimalHistoryOut(BaseModel):
    """档案历史记录返回"""
    id: int
    farm_id: int
    ear_tag: str
    species: str
    breed: str
    pen_id: Optional[int] = None
    gender: str
    birth_date: Optional[date] = None
    in_date: Optional[date] = None
    out_date: Optional[date] = None
    growth_stage: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    sire_tag: Optional[str] = None
    dam_tag: Optional[str] = None
    remark: Optional[str] = None
    delete_time: Optional[date] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnimalHistoryQuery(BaseModel):
    """历史记录列表查询"""
    ear_tag: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10
