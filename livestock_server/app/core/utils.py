"""
公共工具函数

所有 service 层共用的工具函数集中在这里，避免重复代码。
"""
from sqlalchemy.orm import Session


def get_effective_farm_id(db: Session, farm_id: int) -> int:
    """
    获取有效的养殖场 ID。

    如果 farm_id 为 0 或 None（超管未选择时），自动 fallback 到第一个养殖场。
    如果已指定 farm_id，直接返回。
    """
    if farm_id:
        return farm_id
    from app.models.farm import Farm
    farm = db.query(Farm).filter(Farm.deleted == False).order_by(Farm.id).first()
    return farm.id if farm else 0
