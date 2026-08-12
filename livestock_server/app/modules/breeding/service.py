"""
繁育业务逻辑

核心业务规则：
1. 母畜/公畜列表：从档案按「性别 + 可繁育阶段（繁育期/妊娠）」筛选
2. 配种：expected_birth_date = mating_date + 妊娠期（牛280/羊150/猪114），配种后母畜生长阶段自动置"妊娠"
3. 孕检：阳性→成功怀孕；阴性→配种失败，母畜恢复"繁育期"
4. 产犊：存活率自动计算，母畜生长阶段恢复"繁育期"
5. 预警：P2 定时任务自动生成，此处仅提供列表/详情/处理（已处理/已忽略）与手动补录
"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.animal.model import Animal
from app.modules.animal.service import GESTATION_DAYS
from app.modules.breeding.model import MatingRecord, BirthRecord, BreedingAlert
from app.modules.breeding.schema import (
    MatingIn, MatingUpdateIn, PregnancyCheckIn, MatingQuery,
    BirthIn, BirthUpdateIn, BirthQuery,
    AlertIn, AlertHandleIn, AlertQuery,
)

SPECIES = {"牛", "羊", "猪"}
MATING_TYPES = {"本交", "人工受精"}
PREGNANCY_RESULTS = {"阳性", "阴性"}
# 可繁育的生长阶段（"繁育期及以上"）
BREEDING_STAGES = ("繁育期", "妊娠")
ALERT_TYPES = {"孕检", "临产", "未发情"}
ALERT_HANDLE_STATUSES = {"已处理", "已忽略"}


# ============================================================
# 母畜 / 公畜列表（从档案筛选）
# ============================================================

def list_breed_animals(
    db: Session, farm_id: int, gender: str,
    species: Optional[str] = None, keyword: Optional[str] = None,
    page_num: int = 1, page_size: int = 10,
) -> dict:
    """可繁育畜禽列表：按性别 + 繁育期及以上阶段筛选，排除已出栏/死亡"""
    q = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.gender == gender,
        Animal.growth_stage.in_(BREEDING_STAGES),
        Animal.status.in_(("在栏", "种用")),
        Animal.deleted == False,
    )
    if species:
        q = q.filter(Animal.species == species)
    if keyword:
        q = q.filter(Animal.ear_tag.like(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(Animal.ear_tag.asc()).offset((page_num - 1) * page_size).limit(page_size).all()
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def _get_animal(db: Session, farm_id: int, ear_tag: str) -> Animal:
    animal = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.ear_tag == ear_tag,
        Animal.deleted == False,
    ).first()
    if not animal:
        raise BizException(f"档案中不存在耳标 {ear_tag}", code=40101)
    return animal


# ============================================================
# 配种记录
# ============================================================

def list_matings(db: Session, farm_id: int, query: MatingQuery) -> dict:
    """配种记录列表（分页+多条件）"""
    q = db.query(MatingRecord).filter(
        MatingRecord.farm_id == farm_id, MatingRecord.deleted == False
    )
    if query.female_tag:
        q = q.filter(MatingRecord.female_tag == query.female_tag)
    if query.male_tag:
        q = q.filter(MatingRecord.male_tag == query.male_tag)
    if query.species:
        q = q.filter(MatingRecord.species == query.species)
    if query.status:
        q = q.filter(MatingRecord.status == query.status)
    if query.mating_date_start:
        q = q.filter(MatingRecord.mating_date >= query.mating_date_start)
    if query.mating_date_end:
        q = q.filter(MatingRecord.mating_date <= query.mating_date_end)
    total = q.count()
    items = q.order_by(MatingRecord.mating_date.desc(), MatingRecord.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_mating(db: Session, farm_id: int, record_id: int) -> MatingRecord:
    rec = db.query(MatingRecord).filter(
        MatingRecord.id == record_id,
        MatingRecord.farm_id == farm_id,
        MatingRecord.deleted == False,
    ).first()
    if not rec:
        raise BizException("配种记录不存在", code=40110)
    return rec


def add_mating(db: Session, farm_id: int, body: MatingIn, user_id: int) -> MatingRecord:
    """新增配种记录：自动算预产期，母畜生长阶段置"妊娠" """
    if body.species not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40111)
    if body.mating_type not in MATING_TYPES:
        raise BizException(f"配种方式只能是：{'/'.join(sorted(MATING_TYPES))}", code=40112)

    female = _get_animal(db, farm_id, body.female_tag)
    if female.gender != "母":
        raise BizException(f"耳标 {body.female_tag} 不是母畜，不能配种", code=40113)
    if female.growth_stage == "妊娠":
        raise BizException(f"母畜 {body.female_tag} 正处于妊娠状态，不能重复配种", code=40114)

    if body.male_tag:
        male = _get_animal(db, farm_id, body.male_tag)
        if male.gender != "公":
            raise BizException(f"耳标 {body.male_tag} 不是公畜，不能作为父本", code=40115)

    gestation_days = GESTATION_DAYS.get(body.species, 0)
    expected_birth_date = body.mating_date + timedelta(days=gestation_days)

    rec = MatingRecord(
        farm_id=farm_id,
        female_tag=body.female_tag,
        male_tag=body.male_tag,
        species=body.species,
        mating_date=body.mating_date,
        mating_type=body.mating_type,
        semen_source=body.semen_source,
        status="待孕检",
        expected_birth_date=expected_birth_date,
        gestation_days=gestation_days,
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(rec)
    female.growth_stage = "妊娠"
    db.commit()
    return rec


def update_mating(db: Session, farm_id: int, record_id: int, body: MatingUpdateIn) -> MatingRecord:
    """修改配种记录：改配种日期时重算预产期；已孕检的记录不允许改"""
    rec = get_mating(db, farm_id, record_id)
    if rec.pregnancy_check_result:
        raise BizException("该配种记录已登记孕检，不能修改", code=40116)

    data = body.model_dump(exclude_unset=True)
    if data.get("mating_type"):
        if data["mating_type"] not in MATING_TYPES:
            raise BizException(f"配种方式只能是：{'/'.join(sorted(MATING_TYPES))}", code=40112)
    if data.get("male_tag"):
        male = _get_animal(db, farm_id, data["male_tag"])
        if male.gender != "公":
            raise BizException(f"耳标 {data['male_tag']} 不是公畜，不能作为父本", code=40115)

    for k, v in data.items():
        setattr(rec, k, v)
    # 改配种日期 → 重算预产期（妊娠期不变）
    if data.get("mating_date"):
        rec.expected_birth_date = rec.mating_date + timedelta(days=rec.gestation_days or 0)
    db.commit()
    return rec


def delete_mating(db: Session, farm_id: int, record_id: int):
    """删除配种记录：已关联产犊记录禁止删；母畜妊娠标记回退"""
    rec = get_mating(db, farm_id, record_id)
    linked = db.query(BirthRecord).filter(
        BirthRecord.mating_id == record_id, BirthRecord.deleted == False
    ).first()
    if linked:
        raise BizException("该配种记录已关联产犊记录，不能删除", code=40117)
    rec.deleted = True
    _restore_female_stage(db, farm_id, rec.female_tag)
    db.commit()


def pregnancy_check(db: Session, farm_id: int, record_id: int, body: PregnancyCheckIn, user_id: int) -> MatingRecord:
    """孕检登记：阳性→成功怀孕；阴性→配种失败，母畜恢复繁育期"""
    rec = get_mating(db, farm_id, record_id)
    if rec.status == "配种失败":
        raise BizException("该配种记录已判定失败，不能重复孕检", code=40118)
    if body.pregnancy_check_result not in PREGNANCY_RESULTS:
        raise BizException(f"孕检结果只能是：{'/'.join(sorted(PREGNANCY_RESULTS))}", code=40119)

    rec.pregnancy_check_date = body.pregnancy_check_date
    rec.pregnancy_check_result = body.pregnancy_check_result
    if body.remark is not None:
        rec.remark = body.remark

    if body.pregnancy_check_result == "阳性":
        rec.status = "成功怀孕"
    else:
        rec.status = "配种失败"
        _restore_female_stage(db, farm_id, rec.female_tag)
    db.commit()
    return rec


def _restore_female_stage(db: Session, farm_id: int, female_tag: str):
    """配种失败/产犊/删除配种后，若母畜档案仍标记妊娠则恢复繁育期"""
    female = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.ear_tag == female_tag,
        Animal.deleted == False,
    ).first()
    if female and female.growth_stage == "妊娠":
        female.growth_stage = "繁育期"


# ============================================================
# 产犊记录
# ============================================================

def list_births(db: Session, farm_id: int, query: BirthQuery) -> dict:
    """产犊记录列表（分页+多条件）"""
    q = db.query(BirthRecord).filter(
        BirthRecord.farm_id == farm_id, BirthRecord.deleted == False
    )
    if query.female_tag:
        q = q.filter(BirthRecord.female_tag == query.female_tag)
    if query.species:
        q = q.filter(BirthRecord.species == query.species)
    if query.birth_date_start:
        q = q.filter(BirthRecord.birth_date >= query.birth_date_start)
    if query.birth_date_end:
        q = q.filter(BirthRecord.birth_date <= query.birth_date_end)
    total = q.count()
    items = q.order_by(BirthRecord.birth_date.desc(), BirthRecord.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_birth(db: Session, farm_id: int, record_id: int) -> BirthRecord:
    rec = db.query(BirthRecord).filter(
        BirthRecord.id == record_id,
        BirthRecord.farm_id == farm_id,
        BirthRecord.deleted == False,
    ).first()
    if not rec:
        raise BizException("产犊记录不存在", code=40120)
    return rec


def _calc_survival_rate(total_count: int, alive_count: int) -> int:
    return round(alive_count / total_count * 100) if total_count else 0


def _validate_birth_counts(total_count: int, alive_count: int, dead_count: int):
    if alive_count + dead_count > total_count:
        raise BizException("成活数 + 死亡数不能大于产仔总数", code=40121)


def add_birth(db: Session, farm_id: int, body: BirthIn, user_id: int) -> BirthRecord:
    """新增产犊记录：存活率自动计算，母畜生长阶段恢复繁育期"""
    if body.species not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40111)
    female = _get_animal(db, farm_id, body.female_tag)
    if female.gender != "母":
        raise BizException(f"耳标 {body.female_tag} 不是母畜，不能记录产犊", code=40113)
    _validate_birth_counts(body.total_count, body.alive_count, body.dead_count)

    if body.mating_id:
        mating = db.query(MatingRecord).filter(
            MatingRecord.id == body.mating_id,
            MatingRecord.farm_id == farm_id,
            MatingRecord.deleted == False,
        ).first()
        if not mating:
            raise BizException("关联的配种记录不存在", code=40122)

    rec = BirthRecord(
        farm_id=farm_id,
        female_tag=body.female_tag,
        mating_id=body.mating_id,
        species=body.species,
        birth_date=body.birth_date,
        total_count=body.total_count,
        alive_count=body.alive_count,
        dead_count=body.dead_count,
        survival_rate=_calc_survival_rate(body.total_count, body.alive_count),
        offspring_tags=body.offspring_tags,
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(rec)
    _restore_female_stage(db, farm_id, body.female_tag)
    db.commit()
    return rec


def update_birth(db: Session, farm_id: int, record_id: int, body: BirthUpdateIn) -> BirthRecord:
    """修改产犊记录：改产仔数时重算存活率"""
    rec = get_birth(db, farm_id, record_id)
    data = body.model_dump(exclude_unset=True)
    total = data.get("total_count", rec.total_count)
    alive = data.get("alive_count", rec.alive_count)
    dead = data.get("dead_count", rec.dead_count)
    _validate_birth_counts(total, alive, dead)
    if data.get("species") and data["species"] not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40111)
    if data.get("female_tag"):
        female = _get_animal(db, farm_id, data["female_tag"])
        if female.gender != "母":
            raise BizException(f"耳标 {data['female_tag']} 不是母畜", code=40113)
    if data.get("mating_id"):
        mating = db.query(MatingRecord).filter(
            MatingRecord.id == data["mating_id"],
            MatingRecord.farm_id == farm_id,
            MatingRecord.deleted == False,
        ).first()
        if not mating:
            raise BizException("关联的配种记录不存在", code=40122)

    for k, v in data.items():
        setattr(rec, k, v)
    rec.survival_rate = _calc_survival_rate(rec.total_count, rec.alive_count)
    db.commit()
    return rec


def delete_birth(db: Session, farm_id: int, record_id: int):
    rec = get_birth(db, farm_id, record_id)
    rec.deleted = True
    db.commit()


# ============================================================
# 繁育预警（P2 定时任务自动生成，此处列表/详情/处理）
# ============================================================

def add_alert(db: Session, farm_id: int, body: AlertIn, user_id: int) -> BreedingAlert:
    """手动新增预警（供补录/测试，定时任务生成走同一函数）"""
    if body.alert_type not in ALERT_TYPES:
        raise BizException(f"预警类型只能是：{'/'.join(sorted(ALERT_TYPES))}", code=40130)
    rec = BreedingAlert(
        farm_id=farm_id,
        alert_type=body.alert_type,
        animal_tag=body.animal_tag,
        related_id=body.related_id,
        alert_date=body.alert_date,
        alert_content=body.alert_content,
        status="待处理",
    )
    db.add(rec)
    db.commit()
    return rec


def list_alerts(db: Session, farm_id: int, query: AlertQuery) -> dict:
    """繁育预警列表（分页+多条件）"""
    q = db.query(BreedingAlert).filter(
        BreedingAlert.farm_id == farm_id, BreedingAlert.deleted == False
    )
    if query.alert_type:
        q = q.filter(BreedingAlert.alert_type == query.alert_type)
    if query.animal_tag:
        q = q.filter(BreedingAlert.animal_tag == query.animal_tag)
    if query.status:
        q = q.filter(BreedingAlert.status == query.status)
    if query.alert_date_start:
        q = q.filter(BreedingAlert.alert_date >= query.alert_date_start)
    if query.alert_date_end:
        q = q.filter(BreedingAlert.alert_date <= query.alert_date_end)
    total = q.count()
    items = q.order_by(BreedingAlert.alert_date.desc(), BreedingAlert.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_alert(db: Session, farm_id: int, alert_id: int) -> BreedingAlert:
    rec = db.query(BreedingAlert).filter(
        BreedingAlert.id == alert_id,
        BreedingAlert.farm_id == farm_id,
        BreedingAlert.deleted == False,
    ).first()
    if not rec:
        raise BizException("繁育预警不存在", code=40131)
    return rec


def handle_alert(db: Session, farm_id: int, alert_id: int, body: AlertHandleIn, user_id: int) -> BreedingAlert:
    """处理预警：标记已处理/已忽略"""
    if body.status not in ALERT_HANDLE_STATUSES:
        raise BizException(f"处理结果只能是：{'/'.join(sorted(ALERT_HANDLE_STATUSES))}", code=40132)
    rec = get_alert(db, farm_id, alert_id)
    if rec.status != "待处理":
        raise BizException("该预警已处理，不能重复处理", code=40133)
    rec.status = body.status
    rec.handle_time = datetime.now()
    rec.handle_by = user_id
    rec.handle_remark = body.handle_remark
    db.commit()
    return rec
