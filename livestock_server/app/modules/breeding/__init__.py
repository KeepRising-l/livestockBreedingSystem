"""
breeding 繁育模块

- model.py：mating_record / birth_record / breeding_alert
- schema.py：入参 / 出参 / 查询 DTO
- service.py：业务逻辑（预产期计算、母畜阶段联动、存活率计算）
- api.py：路由（router 对外暴露，由 app/api/v1/__init__.py 统一挂载）
"""
from app.modules.breeding.model import MatingRecord, BirthRecord, BreedingAlert  # noqa
from app.modules.breeding.api import router  # noqa

__all__ = ["MatingRecord", "BirthRecord", "BreedingAlert", "router"]
