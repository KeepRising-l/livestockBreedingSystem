"""
畜禽档案模型

耳标规则：5 位 = 畜种位(1位) + 圈舍编号数字(2位) + 入栏序号(2位)
  畜种位：牛=1 / 羊=2 / 猪=3
  例：牛/A02 圈舍第 7 头入栏 -> 10207
带畜种位是因为圈舍编号只在畜种内唯一（牛和羊都可以有 A02），只用编号数字会跨畜种撞号。
耳标空出后可复用（畜禽死亡/出栏后耳标号释放）。
注：本次规则变更前生成的 4 位旧耳标（圈舍ID后两位+序号）仍然有效，不会被改写。

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
    ear_tag = Column(String(10), nullable=False, comment="耳标，5位数字：畜种位+圈舍编号数字+入栏序号")
    species = Column(String(10), nullable=False, comment="畜种：牛/羊/猪")
    breed = Column(String(50), nullable=False, comment="品种，如黄牛/西门塔尔牛")
    pen_id = Column(Integer, nullable=True, comment="所在圈舍ID")
    gender = Column(String(2), nullable=False, comment="性别：公/母")
    birth_date = Column(Date, nullable=True, comment="出生日期")
    in_date = Column(Date, nullable=True, comment="入栏日期")
    out_date = Column(Date, nullable=True, comment="出栏日期")
    growth_stage = Column(String(20), nullable=True, comment="生长阶段")
    physio_status = Column(String(20), nullable=True, comment="母畜生理状态：发情/妊娠/泌乳/休情/淘汰（仅母畜）")
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
    physio_status = Column(String(20), nullable=True, comment="母畜生理状态")
    status = Column(String(20), nullable=True, comment="状态")
    source = Column(String(10), nullable=True, comment="来源")
    sire_tag = Column(String(10), nullable=True, comment="父本耳标")
    dam_tag = Column(String(10), nullable=True, comment="母本耳标")
    remark = Column(Text, nullable=True, comment="备注")
    delete_time = Column(Date, nullable=True, comment="删除日期")
