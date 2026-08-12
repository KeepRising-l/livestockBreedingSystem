# models 包：ORM 模型
# 引入全局基础模型，确保 Base.metadata 能发现这些表（建表时用）。
#
# 模块化重构后，业务模块的模型收敛到 app/modules/*/model.py，
# 它们由 app/api/v1/__init__.py 加载各模块包时连带注册进 Base.metadata，
# 因此这里【不要】再 import app.modules.* 的 model——
# 否则 modules/model.py 里 `from app.models.base import BasePO` 会在
# app.models 首次初始化期间触发循环导入（见 app/modules/health/__init__.py 注释）。
from app.models.base import BasePO  # noqa
from app.models.user import User  # noqa
from app.models.farm import Farm  # noqa
