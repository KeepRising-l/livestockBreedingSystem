"""
system 系统管理模块

- model.py：DictType 字典类型 + DictData 字典数据
- schema.py：入参 / 出参 DTO
- service.py：业务逻辑（含字典初始化 init_dict_data，main.py 启动时调用）
- api.py：路由
"""
from app.modules.system.model import DictType, DictData  # noqa
from app.modules.system.api import router  # noqa

__all__ = ["DictType", "DictData", "router"]
