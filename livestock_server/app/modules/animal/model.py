"""
畜禽档案模型

耳标规则：4 位数 = 前 2 位圈舍编号 + 后 2 位顺序号
耳标空出后可复用（畜禽死亡/出栏后耳标号释放）。

生长阶段（按日龄判断，牛/羊/猪日龄范围不同）：
- 牛：1-60犊牛 61-180保育 181-365生长 366-540育肥 365+可繁育 配种后0-280妊娠
- 羊：1-45羔羊 46-90保育 91-180生长 181-270育肥 300+可繁育 配种后0-150妊娠
- 猪：1-28仔猪 29-70保育 71-120生长 121-180育肥 220+可繁育 配种后0-114妊娠
"""
from datetime import date

from sqlalchemy import Column, String, Integer, Date, Text

from app.models.base import BasePO


class Animal(BasePO):
    __tablename__ = "animal_archive"

    farm_id = Column(Integer, nullable=False, index=True, comment="所属养殖场ID")
    ear_tag = Column(String(10), nullable=False, comment="耳标，4位数字")
    species = Column(String(10), nullable=False, comment="畜种：牛/羊/猪")
    breed = Column(String(50), nullable=False, comment="品种，如黄牛/西门塔尔牛")
    pen_id = Column(Integer, nullable=True, comment="所在圈舍ID")
    gender = Column(String(2), nullable=False, comment="性别：公/母")
    birth_date = Column(Date, nullable=True, comment="出生日期")
    in_date = Column(Date, nullable=True, comment="入栏日期")
    out_date = Column(Date, nullable=True, comment="出栏日期")
    growth_stage = Column(String(20), nullable=True, comment="生长阶段")
    status = Column(String(20), default="在栏", comment="状态：在栏/种用/隔离/待出栏/已出栏/死亡")
    source = Column(String(10), nullable=True, comment="来源：自繁/外购")
    sire_tag = Column(String(10), nullable=True, comment="父本耳标")
    dam_tag = Column(String(10), nullable=True, comment="母本耳标")
    remark = Column(Text, nullable=True, comment="备注")


class AnimalHistory(BasePO):
    """档案历史记录表：删除的档案转入这里，半年后自动清除"""

    __tablename__ = "animal_archive_history"

    farm_id = Column(Integer, nullable=False, index=True, comment="所属养殖场ID")
    ear_tag = Column(String(10), nullable=False, comment="耳标")
    species = Column(String(10), nullable=False, comment="畜种")
    breed = Column(String(50), nullable=False, comment="品种")
    pen_id = Column(Integer, nullable=True, comment="原所在圈舍ID")
    gender = Column(String(2), nullable=False, comment="性别")
    birth_date = Column(Date, nullable=True, comment="出生日期")
    in_date = Column(Date, nullable=True, comment="入栏日期")
    out_date = Column(Date, nullable=True, comment="出栏日期")
    growth_stage = Column(String(20), nullable=True, comment="生长阶段")
    status = Column(String(20), nullable=True, comment="状态")
    source = Column(String(10), nullable=True, comment="来源")
    sire_tag = Column(String(10), nullable=True, comment="父本耳标")
    dam_tag = Column(String(10), nullable=True, comment="母本耳标")
    remark = Column(Text, nullable=True, comment="备注")
    delete_time = Column(Date, nullable=True, comment="删除日期")
