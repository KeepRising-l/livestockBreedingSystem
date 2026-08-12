"""
statistics 统计模块（P3-1）

只读统计模块，无新增表，故无 model.py / schema.py：
- service.py：5 个统计接口的聚合逻辑（dashboard / breeding / health / material / finance）
- api.py：路由（GET /statistics/*，所有登录用户可访问）

统计口径：存栏 = 在栏/种用/隔离/待出栏 的未删除档案；趋势按近 12 个月分组。
"""
from app.modules.statistics.api import router  # noqa

__all__ = ["router"]
