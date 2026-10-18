"""
公共工具函数

所有 service 层共用的工具函数集中在这里，避免重复代码。
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BizException


def get_effective_farm_id(db: Session, farm_id: int) -> int:
    """
    获取有效的养殖场 ID（严格模式，不再回退到第一个农场）。

    farm_id 为 0 或 None（超管未选择养殖场等场景）时抛 40302 业务错误，
    防止误读误写其他养殖场的数据。调用方应先通过 resolve_farm_id()
    或登录用户的 farm_id 拿到有效 ID。
    """
    if not farm_id:
        raise BizException("请先选择目标养殖场", code=40302)
    return farm_id
