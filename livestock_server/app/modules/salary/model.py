"""
薪资配置 ORM 模型

薪资配置表 salary_config：按岗位（饲喂员/兽医/繁育员/库管员）配置基础薪资、奖金比例、扣罚规则。
同一养殖场同一岗位只能有一条配置（service 层做 farm_id + post 唯一校验，删除后可再建）。
"""
from sqlalchemy import Column, String, Integer, Numeric

from app.models.base import BasePO


class SalaryConfig(BasePO):
    """薪资配置表"""
    __tablename__ = "salary_config"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    post = Column(String(20), nullable=False, index=True, comment="岗位：饲喂员/兽医/繁育员/库管员")
    base_salary = Column(Numeric(10, 2), nullable=False, comment="基础薪资（默认 4500/6500/5500/4000）")
    bonus_ratio = Column(Numeric(5, 2), nullable=True, comment="奖金比例（%）")
    deduct_rule = Column(String(255), nullable=True, comment="扣罚规则")
    status = Column(Integer, default=1, comment="状态：1启用 0停用")
    remark = Column(String(255), nullable=True, comment="备注")
