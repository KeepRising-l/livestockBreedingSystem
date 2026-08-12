"""
认证服务：登录、注册

注册流程：
1. 养殖场主注册：创建用户 + 创建养殖场 + 关联 farm_id
2. 员工注册：校验养殖场存在 + 创建用户并绑定 farm_id
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.farm import Farm
from app.schemas.auth import LoginIn, OwnerRegisterIn, EmployeeRegisterIn


def login(db: Session, body: LoginIn) -> dict:
    """登录：支持账号或手机号 + 密码登录，返回 token"""
    user = db.query(User).filter(
        (User.username == body.username) | (User.phone == body.username)
    ).first()
    if not user:
        raise BizException("账号或手机号不存在", code=40001)
    if not verify_password(body.password, user.password):
        raise BizException("密码错误", code=40002)
    if user.status != 1:
        raise BizException("账号已被禁用", code=40003)

    # 把角色信息放进 token，后续接口可直接从 token 取
    token = create_access_token(
        subject=str(user.id),
        extra={
            "user_type": user.user_type,
            "farm_id": user.farm_id or 0,
            "post": user.post or "",
        },
    )
    return {"access_token": token, "token_type": "bearer"}


def register_owner(db: Session, body: OwnerRegisterIn) -> dict:
    """养殖场主注册"""
    # 校验账号唯一
    if db.query(User).filter(User.username == body.username).first():
        raise BizException("账号已存在", code=40004)

    # 1. 创建养殖场
    farm = Farm(
        farm_name=body.farm_name,
        owner_user_id=0,  # 占位，等用户创建后回填
        phone=body.phone,
        livestock_types=body.livestock_types,
        status=1,
    )
    db.add(farm)
    db.flush()  # 拿到 farm.id

    # 2. 创建用户
    user = User(
        username=body.username,
        password=hash_password(body.password),
        real_name=body.real_name,
        phone=body.phone,
        user_type=2,           # 养殖场主
        farm_id=farm.id,
        status=1,
    )
    db.add(user)
    db.flush()  # 拿到 user.id

    # 3. 回填养殖场的 owner_user_id
    farm.owner_user_id = user.id
    db.commit()

    return {"user_id": user.id, "farm_id": farm.id}


def register_employee(db: Session, body_or_farm_id: EmployeeRegisterIn | int, body: EmployeeRegisterIn = None) -> dict:
    """
    员工注册。两种调用方式：
    1. register_employee(db, body) — 原用法，从 body 中取 farm_id
    2. register_employee(db, farm_id, body) — 场主/超管添加，强制 farm_id
    """
    if isinstance(body_or_farm_id, int):
        farm_id_override = body_or_farm_id
    else:
        farm_id_override = None
        body = body_or_farm_id

    # 校验养殖场存在
    fid = farm_id_override if farm_id_override is not None else body.farm_id
    farm = db.query(Farm).filter(Farm.id == fid, Farm.deleted == False).first()
    if not farm:
        raise BizException("养殖场不存在", code=40005)

    # 校验账号唯一
    if db.query(User).filter(User.username == body.username).first():
        raise BizException("账号已存在", code=40004)

    # 创建员工用户
    user = User(
        username=body.username,
        password=hash_password(body.password),
        real_name=body.real_name,
        phone=body.phone,
        user_type=3,           # 员工
        farm_id=fid,
        post=body.post,
        status=1,
    )
    db.add(user)
    db.commit()

    return {"user_id": user.id, "farm_id": fid}
