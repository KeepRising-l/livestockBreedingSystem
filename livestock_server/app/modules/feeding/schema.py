"""
饲喂模块 DTO

入参/出参/查询数据模型。
"""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ============ 饲喂方案 ============

class FeedingPlanIn(BaseModel):
    """新增方案"""
    species: str = Field(..., description="适用种类：cattle/sheep/pig")
    plan_name: str = Field(..., max_length=50, description="方案名称")
    applicable_stage: str = Field(..., description="适用生长阶段")
    applicable_pen_type: Optional[str] = Field(None, description="适用圈舍类型 A/B/C/D")
    feed_times_per_day: int = Field(2, ge=1, le=10, description="每日投喂次数")
    concentrate_weight: Optional[float] = Field(None, description="精料计划重量 kg/只·次")
    silage_weight: Optional[float] = Field(None, description="青贮计划重量 kg/只·次")
    hay_weight: Optional[float] = Field(None, description="干草计划重量 kg/只·次")
    concentrate_price: Optional[float] = Field(None, description="精料单价 元/吨")
    silage_price: Optional[float] = Field(None, description="青贮单价 元/吨")
    hay_price: Optional[float] = Field(None, description="干草单价 元/吨")
    remark: Optional[str] = Field(None, max_length=255)


class FeedingPlanUpdateIn(BaseModel):
    """修改方案"""
    plan_name: Optional[str] = None
    applicable_stage: Optional[str] = None
    applicable_pen_type: Optional[str] = None
    feed_times_per_day: Optional[int] = Field(None, ge=1, le=10)
    concentrate_weight: Optional[float] = None
    silage_weight: Optional[float] = None
    hay_weight: Optional[float] = None
    concentrate_price: Optional[float] = None
    silage_price: Optional[float] = None
    hay_price: Optional[float] = None
    est_cost_per_day: Optional[float] = None
    status: Optional[int] = Field(None, description="0停用 1启用")
    remark: Optional[str] = None


class FeedingPlanOut(BaseModel):
    """方案返回"""
    id: int
    farm_id: int
    species: str
    plan_name: str
    applicable_stage: str
    applicable_pen_type: Optional[str] = None
    feed_times_per_day: int
    concentrate_weight: Optional[float] = None
    silage_weight: Optional[float] = None
    hay_weight: Optional[float] = None
    concentrate_price: Optional[float] = None
    silage_price: Optional[float] = None
    hay_price: Optional[float] = None
    est_cost_per_day: Optional[float] = None
    status: int
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedingPlanQuery(BaseModel):
    """方案列表查询"""
    species: Optional[str] = None
    applicable_stage: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 饲喂记录 ============

class FeedingRecordIn(BaseModel):
    """新增饲喂记录（员工提交，自动进入待审核）"""
    feed_date: date = Field(..., description="饲喂日期")
    time_period: str = Field(..., description="时段：早/晚")
    pen_id: int = Field(..., description="圈舍ID")
    plan_id: Optional[int] = Field(None, description="关联饲喂方案ID")
    actual_concentrate: Optional[float] = Field(None, description="实际精料重量")
    actual_silage: Optional[float] = Field(None, description="实际青贮重量")
    actual_hay: Optional[float] = Field(None, description="实际干草重量")
    animal_count: Optional[int] = Field(None, ge=0, description="饲喂头数")
    status: str = Field("未投喂", description="状态：未投喂/已投喂/已跳过")
    remark: Optional[str] = Field(None, max_length=255)


class FeedingRecordUpdateIn(BaseModel):
    """修改饲喂记录"""
    actual_concentrate: Optional[float] = None
    actual_silage: Optional[float] = None
    actual_hay: Optional[float] = None
    animal_count: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class FeedingRecordBatchItemIn(BaseModel):
    """批量提交里单个圈舍的一条饲喂记录"""
    pen_id: int = Field(..., description="圈舍ID")
    actual_concentrate: Optional[float] = Field(None, ge=0, description="实际精料重量（整圈合计 kg）")
    actual_silage: Optional[float] = Field(None, ge=0, description="实际青贮重量（整圈合计 kg）")
    actual_hay: Optional[float] = Field(None, ge=0, description="实际干草重量（整圈合计 kg）")
    animal_count: Optional[int] = Field(None, ge=0, description="饲喂头数")
    status: Optional[str] = Field(None, description="投喂状态，缺省用批次的统一值")
    remark: Optional[str] = Field(None, max_length=255)


class FeedingRecordBatchIn(BaseModel):
    """
    批量提交饲喂记录：一次提交按多个圈舍生成多条记录

    日期/时段/方案对整批统一，每个圈舍一条明细；同一天同一时段同一圈舍已有记录会被跳过。
    """
    feed_date: date = Field(..., description="饲喂日期")
    time_period: str = Field(..., description="时段：早/晚")
    plan_id: Optional[int] = Field(None, description="关联饲喂方案ID（整批共用）")
    status: str = Field("未投喂", description="投喂状态：未投喂/已投喂/已跳过")
    remark: Optional[str] = Field(None, max_length=255)
    items: List[FeedingRecordBatchItemIn] = Field(..., min_length=1, description="每个圈舍一条")


class FeedingRecordOut(BaseModel):
    """饲喂记录返回"""
    id: int
    farm_id: int
    feed_date: date
    time_period: str
    pen_id: int
    pen_type: Optional[str] = None
    plan_id: Optional[int] = None
    plan_concentrate: Optional[float] = None
    plan_silage: Optional[float] = None
    plan_hay: Optional[float] = None
    actual_concentrate: Optional[float] = None
    actual_silage: Optional[float] = None
    actual_hay: Optional[float] = None
    animal_count: Optional[int] = None
    feed_cost: Optional[float] = None
    status: str
    audit_status: str
    operator_user_id: Optional[int] = None
    feed_time: Optional[datetime] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedingRecordQuery(BaseModel):
    """饲喂记录列表查询"""
    species: Optional[str] = None
    feed_date_start: Optional[date] = None
    feed_date_end: Optional[date] = None
    pen_id: Optional[int] = None
    time_period: Optional[str] = None
    audit_status: Optional[str] = None
    status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10


class AuditActionIn(BaseModel):
    """审核动作"""
    audit_status: str = Field(..., description="目标审核状态：通过/驳回")
    remark: Optional[str] = Field(None, description="审核备注")
