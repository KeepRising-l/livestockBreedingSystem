"""
pen 圈舍模块

- model.py：Pen 圈舍实体
- schema.py：入参 / 出参 DTO
- service.py：业务逻辑（含圈舍自动分配算法）
- api.py：路由

注意：animal 模块依赖本模块 service 的 STAGE_TO_PEN_TYPE / find_available_pen / get_pen，
      引用路径统一为 app.modules.pen.service。
"""
from app.modules.pen.model import Pen  # noqa
from app.modules.pen.api import router  # noqa

__all__ = ["Pen", "router"]
