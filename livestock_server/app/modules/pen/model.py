"""
圈舍模型

四类圈舍：
- pen_type=A：育雏舍，容量 12
- pen_type=B：育成舍，容量 12
- pen_type=C：繁育舍，容量 6
- pen_type=D：种畜圈舍，容量 1

畜种归属（species）：圈舍明确归属某一个畜种，列表按该字段区分牛/羊/猪。
- 新建圈舍时按当前畜种写入
- 尚未分配（NULL）表示"空圈舍、待归属"，列表里仍会展示并标记，首次入栏时自动归属

圈舍编号（pen_code）：**在本畜种的命名空间内唯一**，牛/羊/猪 都可以各自有 A01。
耳标 = 畜种位 + 编号中的 2 位数字 + 入栏序号（共 5 位），例：牛/A02 第 7 头 -> 10207。
因此还有一条约束：**同一畜种内，编号的数字部分不能重复**
（牛/A01 与牛/B01 数字都是 01，会发出相同耳标），由 pen.service 在新增/编辑时校验。
"""
from sqlalchemy import Column, String, Integer

from app.models.base import BasePO


class Pen(BasePO):
    __tablename__ = "pen_info"

    farm_id = Column(Integer, nullable=False, index=True, comment="所属养殖场ID")
    pen_code = Column(String(20), nullable=False, comment="圈舍编号，如 A01；在本畜种内唯一")
    pen_type = Column(String(10), nullable=False, comment="圈舍类型：A/B/C/D")
    species = Column(String(10), nullable=True, index=True, comment="所属畜种：牛/羊/猪；NULL=尚未分配")
    capacity = Column(Integer, nullable=False, default=12, comment="容纳上限")
    current_count = Column(Integer, default=0, comment="当前存栏数")
    status = Column(Integer, default=1, comment="状态：1正常 0空闲")
    remark = Column(String(200), nullable=True, comment="备注")
