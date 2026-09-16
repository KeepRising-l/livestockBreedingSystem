"""
档案 DTO
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _validate_birth_date(v: date) -> date:
    """出生日期校验：必填（由类型非 Optional 保证）、不能晚于今天"""
    if v and v > date.today():
        raise ValueError("出生日期不能晚于今天")
    return v


class AnimalOut(BaseModel):
    """档案信息返回

    age_days / growth_stage 由接口层按出生日期实时计算回填（见 service.to_animal_out），
    保证日龄随时间追溯更新、生长阶段始终匹配当前日龄（存储值由每日调度兜底刷新）。
    """
    id: int
    farm_id: int
    ear_tag: str
    species: str
    breed: str
    pen_id: Optional[int] = None
    gender: str
    birth_date: Optional[date] = None
    age_days: Optional[int] = None  # 日龄 = 今天 - 出生日期，实时计算
    in_date: Optional[date] = None
    out_date: Optional[date] = None
    growth_stage: Optional[str] = None
    physio_status: Optional[str] = None
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
    birth_date: date = Field(..., description="出生日期（必填，用于自动计算日龄和生长阶段）")
    in_date: Optional[date] = None
    status: str = "在栏"
    source: Optional[str] = Field(None, description="来源：自繁/外购")
    sire_tag: Optional[str] = None
    dam_tag: Optional[str] = None
    remark: Optional[str] = None
    pen_id: Optional[int] = Field(None, description="指定圈舍ID，不传则自动分配")

    _check_birth = field_validator("birth_date")(_validate_birth_date)


class AnimalBatchIn(BaseModel):
    """批量入栏请求"""
    species: str = Field(..., description="畜种")
    breed: str = Field(..., description="品种")
    gender: str = Field(..., description="性别：公/母（批量默认同一性别）")
    count: int = Field(..., ge=1, description="入栏数量")
    birth_date: date = Field(..., description="出生日期（必填，用于自动计算日龄和生长阶段）")
    in_date: Optional[date] = None
    status: str = "在栏"
    source: Optional[str] = None
    remark: Optional[str] = None

    _check_birth = field_validator("birth_date")(_validate_birth_date)


class AnimalImportRow(BaseModel):
    """Excel 导入单行（畜种由接口参数统一指定，沿用当前页面物种）"""
    breed: str = Field(..., description="品种")
    gender: str = Field(..., description="性别：公/母")
    birth_date: Optional[date] = None
    in_date: Optional[date] = None
    source: Optional[str] = None
    remark: Optional[str] = None


class AnimalImportIn(BaseModel):
    """Excel 批量导入请求"""
    species: str = Field(..., description="畜种：牛/羊/猪")
    rows: list[AnimalImportRow] = Field(..., min_length=1, description="导入行列表")


class AnimalQuery(BaseModel):
    """档案列表查询"""
    ear_tag: Optional[str] = None
    species: Optional[str] = None
    pen_id: Optional[int] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    physio_status: Optional[str] = None
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
    physio_status: Optional[str] = Field(None, description="母畜生理状态：发情/妊娠/泌乳/休情/淘汰")
    source: Optional[str] = Field(None, description="来源")
    sire_tag: Optional[str] = Field(None, description="父本耳标")
    dam_tag: Optional[str] = Field(None, description="母本耳标")
    remark: Optional[str] = Field(None, description="备注")


class TransferIn(BaseModel):
    """转入其他圈舍（缺口5）"""
    target_pen_id: int = Field(..., description="目标圈舍ID")


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
    physio_status: Optional[str] = None
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
