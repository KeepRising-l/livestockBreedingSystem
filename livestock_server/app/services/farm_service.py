"""
养殖场服务
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.models.farm import Farm
from app.models.user import User
from app.schemas.farm import FarmUpdateIn


def list_all_farms(db: Session) -> list[Farm]:
    """返回所有活跃养殖场（超管专用），按 ID 排序"""
    return db.query(Farm).filter(Farm.deleted == False).order_by(Farm.id).all()


def get_farm_info(db: Session, farm_id: int) -> Farm:
    """获取养殖场信息。farm_id 为 0 时 fallback 到第一个养殖场"""
    farm = None
    if farm_id:
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.deleted == False).first()
    if not farm:
        # 超管或未关联养殖场时，返回第一个养殖场
        farm = db.query(Farm).filter(Farm.deleted == False).order_by(Farm.id).first()
    if not farm:
        raise BizException("养殖场不存在", code=40006)
    return farm


def update_farm(db: Session, farm_id: int, body: FarmUpdateIn) -> Farm:
    """更新养殖场信息"""
    farm = get_farm_info(db, farm_id)
    # 只更新非空字段
    if body.farm_name is not None:
        farm.farm_name = body.farm_name
    if body.phone is not None:
        farm.phone = body.phone
    if body.address is not None:
        farm.address = body.address
    db.commit()
    return farm


def list_employees(db: Session, farm_id: int, page_num: int, page_size: int) -> dict:
    """获取员工列表"""
    query = db.query(User).filter(
        User.farm_id == farm_id,
        User.user_type == 3,
        User.deleted == False,
    )
    total = query.count()
    items = query.offset((page_num - 1) * page_size).limit(page_size).all()
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def update_employee(db: Session, farm_id: int, employee_id: int, data: dict):
    """更新员工信息"""
    from app.core.security import hash_password

    user = db.query(User).filter(
        User.id == employee_id,
        User.farm_id == farm_id,
        User.user_type == 3,
        User.deleted == False,
    ).first()
    if not user:
        raise BizException("员工不存在", code=40007)
    if "username" in data and data["username"]:
        user.username = data["username"]
    if "password" in data and data["password"]:
        user.password = hash_password(data["password"])
    if "real_name" in data:
        user.real_name = data["real_name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "post" in data:
        old_post = user.post
        user.post = data["post"]
        if old_post != user.post:
            # 岗位变化 → 同步 RBAC 岗位角色
            from app.modules.system.service import sync_employee_roles
            sync_employee_roles(db, user.id, user.post)
    if "status" in data:
        user.status = data["status"]
    db.commit()
    return user


def delete_employee(db: Session, farm_id: int, employee_id: int):
    """删除员工（逻辑删除）"""
    user = db.query(User).filter(
        User.id == employee_id,
        User.farm_id == farm_id,
        User.user_type == 3,
        User.deleted == False,
    ).first()
    if not user:
        raise BizException("员工不存在", code=40007)
    user.deleted = True
    db.commit()
