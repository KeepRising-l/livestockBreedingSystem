"""
养殖场模型

养殖场主注册时创建，员工通过 farm_id 关联到养殖场。
livestock_types 存储养殖种类，如 "牛,羊,猪"（多选用逗号分隔）。
"""
from sqlalchemy import Column, String, Integer

from app.models.base import BasePO


class Farm(BasePO):
    __tablename__ = "farm_info"

    farm_name = Column(String(100), nullable=False, comment="养殖场名称")
    owner_user_id = Column(Integer, nullable=False, comment="养殖场主用户ID")
    phone = Column(String(20), nullable=True, comment="联系电话")
    livestock_types = Column(String(50), nullable=False, comment="养殖种类，逗号分隔：牛,羊,猪")
    address = Column(String(200), nullable=True, comment="养殖场地址")
    status = Column(Integer, default=1, comment="状态：1正常 0停用")
