"""
ORM 模型基类

所有表都继承 BasePO，自动带 id、创建时间、更新时间、逻辑删除标记。
"""
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, Boolean

from app.database import Base


class BasePO(Base):
    """
    所有 ORM 模型的基类（PO = Persistent Object）
    提供 4 个公共字段，避免每张表重复写
    """
    __abstract__ = True  # 抽象类，不会单独建表

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    deleted = Column(Boolean, default=False, comment="逻辑删除：0未删 1已删")
