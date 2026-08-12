"""
finance 销售财务模块

- model.py：ORM 实体（sale_order / sale_order_detail / cost_expense / salary_record）
- schema.py：入参 / 出参 / 查询 DTO
- service.py：出栏成本分摊算法、订单/结算、成本支出、利润汇总、薪资生成发放
- api.py：路由（仅场主/超管）
"""
from app.modules.finance.model import (  # noqa
    SaleOrder, SaleOrderDetail, CostExpense, SalaryRecord,
)
from app.modules.finance.api import router  # noqa

__all__ = ["SaleOrder", "SaleOrderDetail", "CostExpense", "SalaryRecord", "router"]
