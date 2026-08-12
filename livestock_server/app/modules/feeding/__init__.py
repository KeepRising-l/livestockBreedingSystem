"""
feeding 饲喂模块

- model.py：FeedingPlan 饲喂方案 + FeedingRecord 饲喂记录
- schema.py：入参 / 出参 DTO
- service.py：业务逻辑
- api.py：路由

依赖：pen 模块的 Pen model。
"""
from app.modules.feeding.model import FeedingPlan, FeedingRecord  # noqa
from app.modules.feeding.api import router  # noqa

__all__ = ["FeedingPlan", "FeedingRecord", "router"]
