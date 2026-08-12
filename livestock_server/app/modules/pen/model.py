"""
圈舍模型

四类圈舍：
- pen_type=A：育雏舍，容量 12
- pen_type=B：育成舍，容量 12
- pen_type=C：繁育舍，容量 6
- pen_type=D：种畜圈舍，容量 1
"""
from sqlalchemy import Column, String, Integer

from app.models.base import BasePO


class Pen(BasePO):
    __tablename__ = "pen_info"

    farm_id = Column(Integer, nullable=False, index=True, comment="所属养殖场ID")
    pen_code = Column(String(20), nullable=False, comment="圈舍编号，如 A10")
    pen_type = Column(String(10), nullable=False, comment="圈舍类型：A/B/C/D")
    capacity = Column(Integer, nullable=False, default=12, comment="容纳上限")
    current_count = Column(Integer, default=0, comment="当前存栏数")
    status = Column(Integer, default=1, comment="状态：1正常 0空闲")
    remark = Column(String(200), nullable=True, comment="备注")
