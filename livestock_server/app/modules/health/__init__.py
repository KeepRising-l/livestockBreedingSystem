"""
health 防疫诊疗模块

模块化样板：一个功能的所有代码收在一个包里。
- model.py：ORM 实体（vaccine_record / medical_record）
- schema.py：入参 / 出参 / 查询 DTO
- service.py：业务逻辑
- api.py：路由（router 对外暴露，由 app/api/v1/__init__.py 统一挂载）

后续新模块（breeding / review / statistics 等）照这个结构复制即可。
"""
from app.modules.health.model import VaccineRecord, MedicalRecord  # noqa
from app.modules.health.api import router  # noqa

__all__ = ["VaccineRecord", "MedicalRecord", "router"]
