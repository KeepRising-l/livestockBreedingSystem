"""
繁育路由

- 母畜/公畜列表：从档案按「性别 + 可繁育日龄」筛选，供配种时选畜
- 配种记录：新增（自动算预产期，提交进待审核）、列表、详情、修改、删除、孕检登记、
  审核（场主/超管，通过后才把母畜置为妊娠 —— 与饲喂记录同一套审核口径）
- 产犊记录：新增（存活率自动算）、列表、详情、修改、删除
- 繁育预警：列表（按需生成当天预警并推送临产站内消息）、详情、手动新增、处理（已处理/已忽略）

说明：繁育日常记录（配种/产犊/预警）所有登录用户可提交，归属校验统一在 service 层按 farm_id 过滤；
      审核类动作（配种记录审核）限场主/超管。
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.perms import require_perms
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.animal.schema import AnimalOut
from app.modules.breeding import service as breeding_service
from app.modules.breeding.schema import (
    MatingIn, MatingUpdateIn, PregnancyCheckIn, MatingOut, MatingQuery, MatingAuditIn,
    BirthIn, BirthUpdateIn, BirthOut, BirthQuery,
    AlertIn, AlertHandleIn, AlertOut, AlertQuery,
    PhysioStatusIn, MaleHealthIn,
)

router = APIRouter(dependencies=[Depends(require_perms("breeding"))])


def _require_farm(current_user: User) -> int:
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    return current_user.farm_id


def _check_owner(current_user: User):
    """养殖场主或超管能操作（user_type=1 或 2），与饲喂记录审核口径一致"""
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)


# ============================================================
# 母畜 / 公畜列表
# ============================================================

@router.get("/females", summary="可繁育母畜列表")
def list_females(
    species: str = Query(None),
    keyword: str = Query(None),
    physio_status: str = Query(None, description="生理状态筛选：正常/发情/妊娠/泌乳/休情/淘汰"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    result = breeding_service.list_breed_animals(
        db, farm_id, "母", species, keyword, physio_status, pageNum, pageSize
    )
    # 显式组装：growth_stage 用繁育口径，并补 age_days / real_growth_stage
    result["list"] = [breeding_service.breed_animal_out(a) for a in result["list"]]
    return Result.ok(data=result)


@router.put("/females/{female_tag}/physio-status", summary="设置母畜生理状态（发情/妊娠/泌乳/休情/淘汰）")
def set_female_physio_status(
    female_tag: str,
    body: PhysioStatusIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    female = breeding_service.set_female_physio_status(
        db, farm_id, female_tag, body.physio_status
    )
    return Result.ok(data=AnimalOut.model_validate(female), msg="生理状态已更新")


@router.get("/males", summary="可繁育公畜列表（含健康档案/使用年限/配种统计）")
def list_males(
    species: str = Query(None),
    keyword: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    result = breeding_service.list_males(db, farm_id, species, keyword, pageNum, pageSize)
    return Result.ok(data=result)


@router.put("/males/{male_tag}/health", summary="编辑公畜健康档案（健康/亚健康/淘汰 + 启用日期）")
def update_male_health(
    male_tag: str,
    body: MaleHealthIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    male = breeding_service.update_male_health(db, farm_id, male_tag, body)
    return Result.ok(data=male, msg="公畜健康档案已更新")


# ============================================================
# 配种记录
# ============================================================

@router.get("/mating/list", summary="配种记录列表")
def list_matings(
    female_tag: str = Query(None),
    male_tag: str = Query(None),
    species: str = Query(None),
    status: str = Query(None),
    audit_status: str = Query(None, description="审核状态：待审核/通过/驳回"),
    mating_date_start: date = Query(None),
    mating_date_end: date = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    query = MatingQuery(
        female_tag=female_tag, male_tag=male_tag, species=species, status=status,
        audit_status=audit_status,
        mating_date_start=mating_date_start, mating_date_end=mating_date_end,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = breeding_service.list_matings(db, farm_id, query)
    result["list"] = [MatingOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/mating/{record_id}", summary="配种记录详情")
def get_mating(record_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.get_mating(db, farm_id, record_id)
    return Result.ok(data=MatingOut.model_validate(rec))


@router.post("/mating/add", summary="新增配种记录（自动算预产期，提交后进待审核）")
def add_mating(body: MatingIn, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.add_mating(db, farm_id, body, current_user.id)
    return Result.ok(data=MatingOut.model_validate(rec), msg="配种记录已提交，等待场主审核")


@router.post("/mating/audit/{record_id}", summary="审核配种记录（场主/超管，通过后才置母畜妊娠）")
def audit_mating(record_id: int, body: MatingAuditIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    rec = breeding_service.audit_mating(
        db, current_user.farm_id, record_id, body.audit_status, body.remark
    )
    return Result.ok(data=MatingOut.model_validate(rec), msg=f"已{body.audit_status}")


@router.put("/mating/update/{record_id}", summary="修改配种记录（已孕检不可改）")
def update_mating(record_id: int, body: MatingUpdateIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.update_mating(db, farm_id, record_id, body)
    return Result.ok(data=MatingOut.model_validate(rec), msg="修改成功")


@router.delete("/mating/{record_id}", summary="删除配种记录（已关联产犊不可删）")
def delete_mating(record_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    breeding_service.delete_mating(db, farm_id, record_id)
    return Result.ok(msg="删除成功")


@router.post("/mating/pregnancy-check/{record_id}", summary="孕检登记（阳性/阴性）")
def pregnancy_check(record_id: int, body: PregnancyCheckIn, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.pregnancy_check(db, farm_id, record_id, body, current_user.id)
    return Result.ok(data=MatingOut.model_validate(rec), msg="孕检已登记")


# ============================================================
# 产犊记录
# ============================================================

@router.get("/birth/list", summary="产犊记录列表")
def list_births(
    female_tag: str = Query(None),
    species: str = Query(None),
    birth_date_start: date = Query(None),
    birth_date_end: date = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    query = BirthQuery(
        female_tag=female_tag, species=species,
        birth_date_start=birth_date_start, birth_date_end=birth_date_end,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = breeding_service.list_births(db, farm_id, query)
    result["list"] = [BirthOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/birth/{record_id}", summary="产犊记录详情")
def get_birth(record_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.get_birth(db, farm_id, record_id)
    return Result.ok(data=BirthOut.model_validate(rec))


@router.post("/birth/add", summary="新增产犊记录（存活率自动计算）")
def add_birth(body: BirthIn, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.add_birth(db, farm_id, body, current_user.id)
    return Result.ok(data=BirthOut.model_validate(rec), msg="产犊记录已登记")


@router.put("/birth/update/{record_id}", summary="修改产犊记录")
def update_birth(record_id: int, body: BirthUpdateIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.update_birth(db, farm_id, record_id, body)
    return Result.ok(data=BirthOut.model_validate(rec), msg="修改成功")


@router.delete("/birth/{record_id}", summary="删除产犊记录")
def delete_birth(record_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    breeding_service.delete_birth(db, farm_id, record_id)
    return Result.ok(msg="删除成功")


# ============================================================
# 繁育预警
# ============================================================

@router.get("/alert/list", summary="繁育预警列表")
def list_alerts(
    alert_type: str = Query(None),
    species: str = Query(None, description="畜种：牛/羊/猪"),
    animal_tag: str = Query(None),
    status: str = Query(None),
    alert_date_start: date = Query(None),
    alert_date_end: date = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    # 按需生成：打开预警页面即可看到当天预警，不再依赖 00:10 定时任务常驻。
    # 生成失败只记日志，不能影响列表查询（try 内已提交，失败时回滚本场本次生成）。
    try:
        breeding_service.ensure_alerts(db, farm_id)
    except Exception as e:
        db.rollback()
        logger.warning(f"繁育预警按需生成失败（farm_id={farm_id}）：{e}")
    query = AlertQuery(
        alert_type=alert_type, species=species, animal_tag=animal_tag, status=status,
        alert_date_start=alert_date_start, alert_date_end=alert_date_end,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = breeding_service.list_alerts(db, farm_id, query)
    result["list"] = [AlertOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/alert/{alert_id}", summary="繁育预警详情")
def get_alert(alert_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.get_alert(db, farm_id, alert_id)
    return Result.ok(data=AlertOut.model_validate(rec))


@router.post("/alert/add", summary="手动新增繁育预警（供补录/测试）")
def add_alert(body: AlertIn, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.add_alert(db, farm_id, body, current_user.id)
    return Result.ok(data=AlertOut.model_validate(rec), msg="预警已生成")


@router.post("/alert/handle/{alert_id}", summary="处理繁育预警（已处理/已忽略）")
def handle_alert(alert_id: int, body: AlertHandleIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.handle_alert(db, farm_id, alert_id, body, current_user.id)
    return Result.ok(data=AlertOut.model_validate(rec), msg="预警已处理")
