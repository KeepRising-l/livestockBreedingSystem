"""
系统管理模型：字典类型 + 字典数据
"""
from sqlalchemy import Column, String, Integer, Text

from app.models.base import BasePO


class DictType(BasePO):
    """字典类型表"""
    __tablename__ = "sys_dict_type"

    dict_name = Column(String(50), nullable=False, comment="字典名称")
    dict_type = Column(String(50), nullable=False, unique=True, index=True, comment="字典类型（唯一标识）")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0停用")
    remark = Column(String(255), nullable=True, comment="备注")


class DictData(BasePO):
    """字典数据表"""
    __tablename__ = "sys_dict_data"

    dict_type = Column(String(50), nullable=False, index=True, comment="字典类型")
    dict_label = Column(String(50), nullable=False, comment="字典标签")
    dict_value = Column(String(50), nullable=False, comment="字典键值")
    dict_sort = Column(Integer, nullable=False, default=0, comment="排序")
    dict_extra = Column(Text, nullable=True, comment="扩展信息（JSON，如品种对应的畜种）")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0停用")
