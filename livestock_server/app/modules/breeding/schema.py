"""
繁育 DTO

- MatingRecord：配种记录（expected_birth_date 由 service 按妊娠期自动计算）
- BirthRecord：产犊记录（survival_rate 由 service 自动计算）
- BreedingAlert：繁育预警（列表 + 处理，P2 定时任务自动生成）
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============ 母畜生理状态 ============

class PhysioStatusIn(BaseModel):
    """设置母畜生理状态"""
    physio_status: str = Field(..., max_length=20, description="生理状态：正常/发情/妊娠/泌乳/休情/淘汰")


# ============ 公畜健康档案 ============

class MaleHealthIn(BaseModel):
    """编辑公畜健康档案（缺口4）"""
    health_status: Optional[str] = Field(None, max_length=10, description="健康状态：健康/亚健康/淘汰")
    use_start_date: Optional[date] = Field(None, description="启用日期（使用年限计算起点）")
    semen_quality: Optional[str] = Field(None, max_length=255, description="精液质量备注")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


# ============ 配种记录 ============

class MatingIn(BaseModel):
    """新增配种记录（提交后进待审核，审核通过才置母畜为妊娠）"""
    female_tag: str = Field(..., max_length=10, description="母畜耳标")
    male_tag: Optional[str] = Field(None, max_length=10, description="公畜耳标")
    species: str = Field(..., max_length=10, description="养殖种类：牛/羊/猪")
    mating_date: date = Field(..., description="配种日期")
    mating_type: str = Field("本交", max_length=10, description="配种方式：本交/人工受精")
    semen_source: Optional[str] = Field(None, max_length=100, description="精液来源")
    remark: Optional[str] = Field(None, max_length=255)


class MatingAuditIn(BaseModel):
    """审核配种记录（场主/超管）"""
    audit_status: str = Field(..., description="目标审核状态：通过/驳回")
    remark: Optional[str] = Field(None, max_length=255, description="审核备注")


class MatingUpdateIn(BaseModel):
    """修改配种记录（仅未生产前可改）"""
    male_tag: Optional[str] = None
    mating_date: Optional[date] = None
    mating_type: Optional[str] = None
    semen_source: Optional[str] = None
    remark: Optional[str] = None


class PregnancyCheckIn(BaseModel):
    """孕检登记"""
    pregnancy_check_date: date = Field(..., description="孕检日期")
    pregnancy_check_result: str = Field(..., max_length=10, description="孕检结果：阳性/阴性")
    remark: Optional[str] = Field(None, max_length=255)


class MatingOut(BaseModel):
    """配种记录返回"""
    id: int
    farm_id: int
    female_tag: str
    male_tag: Optional[str] = None
    species: str
    mating_date: date
    mating_type: str
    semen_source: Optional[str] = None
    status: str
    audit_status: str
    pregnancy_check_date: Optional[date] = None
    pregnancy_check_result: Optional[str] = None
    expected_birth_date: Optional[date] = None
    remain_days: Optional[int] = None
    gestation_days: Optional[int] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatingQuery(BaseModel):
    """配种记录列表查询"""
    female_tag: Optional[str] = None
    male_tag: Optional[str] = None
    species: Optional[str] = None
    status: Optional[str] = None
    audit_status: Optional[str] = None
    mating_date_start: Optional[date] = None
    mating_date_end: Optional[date] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 产犊记录 ============

class BirthIn(BaseModel):
    """新增产犊记录"""
    female_tag: str = Field(..., max_length=10, description="母畜耳标")
    mating_id: Optional[int] = Field(None, description="关联配种记录ID")
    species: str = Field(..., max_length=10, description="养殖种类：牛/羊/猪")
    birth_date: date = Field(..., description="生产日期")
    total_count: int = Field(0, ge=0, description="产仔总数")
    alive_count: int = Field(0, ge=0, description="成活数量")
    dead_count: int = Field(0, ge=0, description="死亡数量")
    offspring_tags: Optional[str] = Field(None, max_length=255, description="仔畜耳标列表（逗号分隔）")
    remark: Optional[str] = Field(None, max_length=255)


class BirthUpdateIn(BaseModel):
    """修改产犊记录"""
    female_tag: Optional[str] = None
    mating_id: Optional[int] = None
    species: Optional[str] = None
    birth_date: Optional[date] = None
    total_count: Optional[int] = None
    alive_count: Optional[int] = None
    dead_count: Optional[int] = None
    offspring_tags: Optional[str] = None
    remark: Optional[str] = None


class BirthOut(BaseModel):
    """产犊记录返回"""
    id: int
    farm_id: int
    female_tag: str
    mating_id: Optional[int] = None
    species: str
    birth_date: date
    total_count: int
    alive_count: int
    dead_count: int
    survival_rate: Optional[int] = None
    offspring_tags: Optional[str] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class BirthQuery(BaseModel):
    """产犊记录列表查询"""
    female_tag: Optional[str] = None
    species: Optional[str] = None
    birth_date_start: Optional[date] = None
    birth_date_end: Optional[date] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 繁育预警 ============

class AlertIn(BaseModel):
    """手动新增繁育预警（定时任务自动生成，此接口供补录/测试）"""
    alert_type: str = Field(..., max_length=10, description="预警类型：孕检/临产/未发情")
    animal_tag: str = Field(..., max_length=10, description="关联耳标")
    related_id: Optional[int] = Field(None, description="关联业务记录ID")
    alert_date: date = Field(..., description="预警日期")
    alert_content: Optional[str] = Field(None, max_length=255, description="预警内容")


class AlertHandleIn(BaseModel):
    """处理预警"""
    status: str = Field(..., max_length=10, description="处理结果：已处理/已忽略")
    handle_remark: Optional[str] = Field(None, max_length=255, description="处理备注")


class AlertOut(BaseModel):
    """繁育预警返回"""
    id: int
    farm_id: int
    alert_type: str
    animal_tag: str
    related_id: Optional[int] = None
    alert_date: date
    alert_content: Optional[str] = None
    status: str
    handle_time: Optional[datetime] = None
    handle_by: Optional[int] = None
    handle_remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertQuery(BaseModel):
    """繁育预警列表查询"""
    alert_type: Optional[str] = None
    species: Optional[str] = None
    animal_tag: Optional[str] = None
    status: Optional[str] = None
    alert_date_start: Optional[date] = None
    alert_date_end: Optional[date] = None
    pageNum: int = 1
    pageSize: int = 10
