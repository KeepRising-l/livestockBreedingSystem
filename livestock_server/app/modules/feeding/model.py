"""
饲喂模块 ORM 模型

- FeedingPlan：饲喂方案（按畜种+生长阶段配置，每只每次投喂多少精料/青贮/干草）
- FeedingRecord：饲喂记录（每天每圈舍每时段一条，员工提交后进入审核）
"""
from datetime import date, datetime

from sqlalchemy import Column, String, Integer, DateTime, Date, Numeric, UniqueConstraint

from app.models.base import BasePO


class FeedingPlan(BasePO):
    """饲喂方案表"""
    __tablename__ = "feeding_plan"
    __table_args__ = (
        # 同一养殖场下，方案名称不能重复
        UniqueConstraint("farm_id", "plan_name", name="uk_farm_plan_name"),
    )

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    species = Column(String(10), nullable=False, index=True, comment="适用种类：cattle/sheep/pig")
    plan_name = Column(String(50), nullable=False, comment="方案名称")
    applicable_stage = Column(String(50), nullable=False, comment="适用生长阶段，如保育期/生长期")
    applicable_pen_type = Column(String(10), nullable=True, comment="适用圈舍类型 A/B/C/D")
    feed_times_per_day = Column(Integer, nullable=False, default=2, comment="每日投喂次数")
    concentrate_weight = Column(Numeric(8, 2), nullable=True, comment="精料计划重量 kg/只·次")
    silage_weight = Column(Numeric(8, 2), nullable=True, comment="青贮计划重量 kg/只·次")
    hay_weight = Column(Numeric(8, 2), nullable=True, comment="干草计划重量 kg/只·次")
    concentrate_price = Column(Numeric(10, 2), nullable=True, comment="精料单价 元/吨")
    silage_price = Column(Numeric(10, 2), nullable=True, comment="青贮单价 元/吨")
    hay_price = Column(Numeric(10, 2), nullable=True, comment="干草单价 元/吨")
    est_cost_per_day = Column(Numeric(10, 2), nullable=True, comment="预计单只日成本")
    status = Column(Integer, default=1, comment="状态：0停用 1启用")
    remark = Column(String(255), nullable=True, comment="备注")


class FeedingRecord(BasePO):
    """饲喂记录表"""
    __tablename__ = "feeding_record"
    __table_args__ = (
        # 联合索引：养殖场 + 日期 + 时段，方便按天查饲喂情况
        UniqueConstraint("farm_id", "feed_date", "time_period", "pen_id", name="uk_farm_date_period_pen"),
    )

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    feed_date = Column(Date, nullable=False, index=True, comment="饲喂日期")
    time_period = Column(String(4), nullable=False, comment="时段：早/晚")
    pen_id = Column(Integer, nullable=False, index=True, comment="圈舍ID")
    pen_type = Column(String(2), nullable=True, comment="圈舍类型")
    plan_id = Column(Integer, nullable=True, index=True, comment="关联饲喂方案ID")
    plan_concentrate = Column(Numeric(8, 2), nullable=True, comment="计划精料重量")
    plan_silage = Column(Numeric(8, 2), nullable=True, comment="计划青贮重量")
    plan_hay = Column(Numeric(8, 2), nullable=True, comment="计划干草重量")
    actual_concentrate = Column(Numeric(8, 2), nullable=True, comment="实际精料重量")
    actual_silage = Column(Numeric(8, 2), nullable=True, comment="实际青贮重量")
    actual_hay = Column(Numeric(8, 2), nullable=True, comment="实际干草重量")
    animal_count = Column(Integer, nullable=True, comment="饲喂头数")
    feed_cost = Column(Numeric(10, 2), nullable=True, comment="本次饲喂成本")
    status = Column(String(10), default="未投喂", comment="状态：未投喂/已投喂/已跳过")
    audit_status = Column(String(10), default="待审核", comment="审核状态：待审核/通过/驳回")
    operator_user_id = Column(Integer, nullable=True, index=True, comment="负责人ID")
    feed_time = Column(DateTime, nullable=True, comment="实际投喂时间")
    remark = Column(String(255), nullable=True, comment="备注")
