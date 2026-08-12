"""
review 审核模块

统一审核入口：聚合查询五类业务待审核记录 + 转发审核到各模块。
- model.py：说明性文件（无新表，审核状态落各业务表 audit_status）
- schema.py：统一待审核项 / 审核动作 DTO
- service.py：聚合查询 + 转发审核
- api.py：路由（router 对外暴露，由 app/api/v1/__init__.py 统一挂载）
"""
from app.modules.review.api import router  # noqa

__all__ = ["router"]
