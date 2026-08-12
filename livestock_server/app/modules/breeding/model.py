"""
繁育 ORM 模型

三张表：
- MatingRecord：配种记录（母畜 + 公畜，expected_birth_date = 配种日期 + 妊娠期）
- BirthRecord：产犊记录（关联配种记录，记录产仔数与仔畜耳标）
- BreedingAlert：繁育预警（孕检/临产/未发情，P2 定时任务自动生成，此处仅存储与处理）
"""
from datetime import date, datetime

from sqlalchemy import Column, String, Integer, Date, DateTime

from app.models.base import BasePO


class MatingRecord(BasePO):
    """配种记录表"""
    __tablename__ = "mating_record"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    female_tag = Column(String(10), nullable=False, index=True, comment="母畜耳标")
    male_tag = Column(String(10), nullable=True, comment="公畜耳标")
    species = Column(String(10), nullable=False, comment="养殖种类：牛/羊/猪")
    mating_date = Column(Date, nullable=False, index=True, comment="配种日期")
    mating_type = Column(String(10), nullable=False, default="本交", comment="配种方式：本交/人工受精")
    semen_source = Column(String(100), nullable=True, comment="精液来源（人工受精时填写）")
    status = Column(String(10), nullable=False, default="待孕检", comment="状态：待孕检/成功怀孕/配种失败")
    pregnancy_check_date = Column(Date, nullable=True, comment="孕检日期")
    pregnancy_check_result = Column(String(10), nullable=True, comment="孕检结果：阳性/阴性")
    expected_birth_date = Column(Date, nullable=True, index=True, comment="预计生产日期")
    gestation_days = Column(Integer, nullable=True, comment="妊娠期天数（牛280/羊150/猪114）")
    operator_user_id = Column(Integer, nullable=True, comment="操作人ID")
    remark = Column(String(255), nullable=True, comment="备注")

    @property
    def remain_days(self) -> int | None:
        """剩余生产天数（运行时计算）"""
        if not self.expected_birth_date:
            return None
        return (self.expected_birth_date - date.today()).days


class BirthRecord(BasePO):
    """产犊记录表"""
    __tablename__ = "birth_record"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    female_tag = Column(String(10), nullable=False, index=True, comment="母畜耳标")
    mating_id = Column(Integer, nullable=True, comment="关联配种记录ID")
    species = Column(String(10), nullable=False, comment="养殖种类：牛/羊/猪")
    birth_date = Column(Date, nullable=False, index=True, comment="生产日期")
    total_count = Column(Integer, nullable=False, default=0, comment="产仔总数")
    alive_count = Column(Integer, nullable=False, default=0, comment="成活数量")
    dead_count = Column(Integer, nullable=False, default=0, comment="死亡数量")
    survival_rate = Column(Integer, nullable=True, comment="成活率（%）")
    offspring_tags = Column(String(255), nullable=True, comment="仔畜耳标列表（逗号分隔）")
    operator_user_id = Column(Integer, nullable=True, comment="操作人ID")
    remark = Column(String(255), nullable=True, comment="备注")


class BreedingAlert(BasePO):
    """繁育预警表"""
    __tablename__ = "breeding_alert"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    alert_type = Column(String(10), nullable=False, index=True, comment="预警类型：孕检/临产/未发情")
    animal_tag = Column(String(10), nullable=False, index=True, comment="关联耳标")
    related_id = Column(Integer, nullable=True, comment="关联业务记录ID")
    alert_date = Column(Date, nullable=False, index=True, comment="预警日期")
    alert_content = Column(String(255), nullable=True, comment="预警内容")
    status = Column(String(10), nullable=False, default="待处理", comment="状态：待处理/已处理/已忽略")
    handle_time = Column(DateTime, nullable=True, comment="处理时间")
    handle_by = Column(Integer, nullable=True, comment="处理人ID")
    handle_remark = Column(String(255), nullable=True, comment="处理备注")
