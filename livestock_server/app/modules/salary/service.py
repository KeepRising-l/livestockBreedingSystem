"""
薪资配置业务逻辑

规则：
1. 同一养殖场同一岗位只能有一条配置（farm_id + post 唯一，service 层校验）
2. 岗位取值限定：饲喂员/兽医/繁育员/库管员（与字典 sys_post、用户表 post 一致）
3. 岗位新增时若不填基础薪资，可用各岗位默认值（前端带出）；后端只校验必填
4. 权限（仅场主/超管）在 api 层校验
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.salary.model import SalaryConfig
from app.modules.salary.schema import (
    SalaryConfigIn, SalaryConfigUpdateIn, SalaryConfigQuery,
)

# 岗位白名单（与字典 sys_post、用户表 post 一致）
POSTS = ("饲喂员", "兽医", "繁育员", "库管员")
# 岗位默认基础薪资（DBD 6.2）
DEFAULT_SALARY = {"饲喂员": 4500, "兽医": 6500, "繁育员": 5500, "库管员": 4000}


def list_configs(db: Session, farm_id: int, query: SalaryConfigQuery) -> dict:
    """薪资配置列表（分页 + 岗位/状态筛选）"""
    q = db.query(SalaryConfig).filter(
        SalaryConfig.farm_id == farm_id, SalaryConfig.deleted == False
    )
    if query.post:
        q = q.filter(SalaryConfig.post == query.post)
    if query.status is not None:
        q = q.filter(SalaryConfig.status == query.status)

    total = q.count()
    items = q.order_by(SalaryConfig.id.asc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_config(db: Session, farm_id: int, config_id: int) -> SalaryConfig:
    conf = db.query(SalaryConfig).filter(
        SalaryConfig.id == config_id,
        SalaryConfig.farm_id == farm_id,
        SalaryConfig.deleted == False,
    ).first()
    if not conf:
        raise BizException("薪资配置不存在", code=40400)
    return conf


def add_config(db: Session, farm_id: int, body: SalaryConfigIn) -> SalaryConfig:
    """新增薪资配置（同一岗位只能配一条）"""
    _validate_post(body.post)
    _check_post_unique(db, farm_id, body.post)

    conf = SalaryConfig(
        farm_id=farm_id,
        post=body.post,
        base_salary=body.base_salary,
        bonus_ratio=body.bonus_ratio,
        deduct_rule=body.deduct_rule,
        status=body.status,
        remark=body.remark,
    )
    db.add(conf)
    db.commit()
    return conf


def update_config(db: Session, farm_id: int, config_id: int, body: SalaryConfigUpdateIn) -> SalaryConfig:
    """修改薪资配置（岗位作为唯一 key，不可改）"""
    conf = get_config(db, farm_id, config_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(conf, k, v)
    db.commit()
    return conf


def delete_config(db: Session, farm_id: int, config_id: int):
    conf = get_config(db, farm_id, config_id)
    conf.deleted = True
    db.commit()


def _validate_post(post: str):
    if post not in POSTS:
        raise BizException(f"岗位只能是：{'/'.join(POSTS)}", code=40401)


def _check_post_unique(db: Session, farm_id: int, post: str):
    exists = db.query(SalaryConfig).filter(
        SalaryConfig.farm_id == farm_id,
        SalaryConfig.post == post,
        SalaryConfig.deleted == False,
    ).first()
    if exists:
        raise BizException(f"岗位【{post}】的薪资配置已存在", code=40402)
