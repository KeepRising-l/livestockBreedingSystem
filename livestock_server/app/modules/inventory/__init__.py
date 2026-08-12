"""
inventory 物资库存模块

- model.py：MaterialStock 库存 + MaterialPurchase 进货 + MaterialConsume 领用
- schema.py：入参 / 出参 DTO（含 AuditActionIn，被 health 模块复用）
- service.py：业务逻辑（进货/领用审核后增减库存）
- api.py：路由
"""
from app.modules.inventory.model import MaterialStock, MaterialPurchase, MaterialConsume  # noqa
from app.modules.inventory.api import router  # noqa

__all__ = ["MaterialStock", "MaterialPurchase", "MaterialConsume", "router"]
