"""
salary 薪资配置模块

- model.py：ORM 实体（salary_config）
- schema.py：入参 / 出参 / 查询 DTO
- service.py：业务逻辑（岗位唯一校验等）
- api.py：路由（仅场主/超管可配置）
"""
from app.modules.salary.model import SalaryConfig  # noqa
from app.modules.salary.api import router  # noqa

__all__ = ["SalaryConfig", "router"]
