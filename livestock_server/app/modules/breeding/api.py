"""
繁育路由

- 母畜/公畜列表：从档案按「性别 + 可繁育阶段」筛选，供配种时选畜
- 配种记录：新增（自动算预产期）、列表、详情、修改、删除、孕检登记
- 产犊记录：新增（存活率自动算）、列表、详情、修改、删除
- 繁育预警：列表、详情、手动新增、处理（已处理/已忽略）

说明：繁育记录为日常生产记录（DBD 无审核字段），所有登录用户可操作，
      归属校验统一在 service 层按 farm_id 过滤。
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
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
    MatingIn, MatingUpdateIn, PregnancyCheckIn, MatingOut, MatingQuery,
    BirthIn, BirthUpdateIn, BirthOut, BirthQuery,
    AlertIn, AlertHandleIn, AlertOut, AlertQuery,
)

router = APIRouter(dependencies=[Depends(require_perms("breeding"))])


def _require_farm(current_user: User) -> int:
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    return current_user.farm_id


# ============================================================
# 母畜 / 公畜列表
# ============================================================

@router.get("/females", summary="可繁育母畜列表")
def list_females(
    species: str = Query(None),
    keyword: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    result = breeding_service.list_breed_animals(db, farm_id, "母", species, keyword, pageNum, pageSize)
    result["list"] = [AnimalOut.model_validate(a) for a in result["list"]]
    return Result.ok(data=result)


@router.get("/males", summary="可繁育公畜列表")
def list_males(
    species: str = Query(None),
    keyword: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    result = breeding_service.list_breed_animals(db, farm_id, "公", species, keyword, pageNum, pageSize)
    result["list"] = [AnimalOut.model_validate(a) for a in result["list"]]
    return Result.ok(data=result)


# ============================================================
# 配种记录
# ============================================================

@router.get("/mating/list", summary="配种记录列表")
def list_matings(
    female_tag: str = Query(None),
    male_tag: str = Query(None),
    species: str = Query(None),
    status: str = Query(None),
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


@router.post("/mating/add", summary="新增配种记录（自动算预产期）")
def add_mating(body: MatingIn, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    rec = breeding_service.add_mating(db, farm_id, body, current_user.id)
    return Result.ok(data=MatingOut.model_validate(rec), msg="配种记录已登记")


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
    query = AlertQuery(
        alert_type=alert_type, animal_tag=animal_tag, status=status,
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
