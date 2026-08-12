"""
animal 档案模块

- model.py：Animal 畜禽档案 + AnimalHistory 历史记录
- schema.py：入参 / 出参 DTO
- service.py：业务逻辑（耳标生成、圈舍分配、生长阶段判定）
- api.py：路由

依赖：pen 模块 service 的 STAGE_TO_PEN_TYPE / find_available_pen / get_pen。
"""
from app.modules.animal.model import Animal, AnimalHistory  # noqa
from app.modules.animal.api import router  # noqa

__all__ = ["Animal", "AnimalHistory", "router"]
