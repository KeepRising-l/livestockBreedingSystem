"""
繁育业务逻辑

核心业务规则：
1. 母畜/公畜列表：从档案按「性别 + 可繁育日龄（按出生日期实时判定，牛365/羊300/猪220）」筛选
2. 配种：expected_birth_date = mating_date + 妊娠期（牛280/羊150/猪114）；
   提交后进「待审核」，场主/超管审核通过才把母畜置为「妊娠」（与饲喂记录同一套审核口径）
3. 孕检：阳性→成功怀孕；阴性→配种失败，母畜恢复"繁育期"
4. 产犊：存活率自动计算，母畜生长阶段恢复"繁育期"
5. 预警：规则统一收敛在本模块 ensure_alerts()，列表接口按需生成 + 每日 00:10 定时任务兜底；
   此处提供列表/详情/处理（已处理/已忽略）与手动补录，配种相关预警只统计「已审核通过」的记录
6. 母畜/公畜列表返回的 growth_stage 为繁育展示口径（繁育期/妊娠），
   real_growth_stage 为按出生日期实时计算的档案真实阶段（如育肥期）
"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.animal.model import Animal
from app.modules.animal.service import (
    BREEDABLE_AGE,
    GESTATION_DAYS,
    PHYSIO_STATUSES,
    determine_growth_stage,
    to_animal_out,
)
from app.modules.breeding.model import MatingRecord, BirthRecord, BreedingAlert, BreedingMale
from app.modules.breeding.schema import (
    MatingIn, MatingUpdateIn, PregnancyCheckIn, MatingQuery,
    BirthIn, BirthUpdateIn, BirthQuery,
    AlertIn, AlertHandleIn, AlertQuery,
    MaleHealthIn,
)

SPECIES = {"牛", "羊", "猪"}
MATING_TYPES = {"本交", "人工受精"}
PREGNANCY_RESULTS = {"阳性", "阴性"}
# 注：可繁育筛选已改为按出生日期实时判定（见 list_breed_animals），
# 不再依赖 animal_archive.growth_stage 的「繁育期/妊娠」取值。
ALERT_TYPES = {"孕检", "临产", "未发情"}
ALERT_HANDLE_STATUSES = {"已处理", "已忽略"}
MALE_HEALTH_STATUSES = {"健康", "亚健康", "淘汰"}

# 预警规则常量（天）：列表接口按需生成与每日定时任务共用，避免规则双份维护
PREGNANCY_CHECK_DAYS = 60   # 配种后满 60 天 → 孕检提醒
BIRTH_REMIND_DAYS = 15      # 预产期前 15 天（含已逾期）→ 临产提醒
HEAT_REMIND_DAYS = 60       # 产犊后满 60 天仍无配种 → 未发情提醒


# ============================================================
# 母畜 / 公畜列表（从档案筛选）
# ============================================================

def list_breed_animals(
    db: Session, farm_id: int, gender: str,
    species: Optional[str] = None, keyword: Optional[str] = None,
    physio_status: Optional[str] = None,
    page_num: int = 1, page_size: int = 10,
) -> dict:
    """
    可繁育畜禽列表：排除已出栏/死亡/已淘汰。

    「可繁育」= 按出生日期算出的日龄达到该畜种的可繁育起始日龄（牛365/羊300/猪220），
    实时判定而不是读 animal_archive.growth_stage —— 那一列只在入栏时写一次 + 每日 00:05
    调度刷新，长期会陈旧错乱（实测有 16 天龄的犊牛被存成"繁育期"、350 天龄的母羊还是"保育期"），
    直接拿来筛会出现"页面上一个可繁育的都选不到"。
    保留 growth_stage='妊娠' 的条件，兼容出生日期缺失但已确认妊娠的存量数据。
    """
    today = date.today()
    age_conds = [
        and_(Animal.species == sp, Animal.birth_date.isnot(None),
             Animal.birth_date <= today - timedelta(days=days))
        for sp, days in BREEDABLE_AGE.items()
    ]
    q = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.gender == gender,
        or_(or_(*age_conds), Animal.growth_stage == "妊娠"),
        Animal.status.in_(("在栏", "种用")),
        Animal.deleted == False,
        # 已淘汰的母畜不参与繁育选畜（or_ 兼容历史 NULL 数据）
        or_(Animal.physio_status.is_(None), Animal.physio_status != "淘汰"),
    )
    if species:
        q = q.filter(Animal.species == species)
    if keyword:
        q = q.filter(Animal.ear_tag.like(f"%{keyword}%"))
    if physio_status:
        q = q.filter(Animal.physio_status == physio_status)
    total = q.count()
    items = q.order_by(Animal.ear_tag.asc()).offset((page_num - 1) * page_size).limit(page_size).all()
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def breed_animal_out(a: Animal) -> dict:
    """
    组装母畜/公畜列表返回字段（繁育模块口径）。

    为什么不能直接返回 ORM 的 growth_stage：该列只在入栏时写一次 + 每日 00:05 刷新，
    会长期陈旧（例如 373 日龄的牛被存成"生长期"）。繁育档案展示口径与档案真实阶段拆开：
    - age_days：按出生日期实时计算；
    - growth_stage：繁育展示口径 —— 已确认妊娠显示"妊娠"，其余达到可繁育日龄的显示"繁育期"；
    - real_growth_stage：档案真实生长阶段，按出生日期实时计算（妊娠个体也保留如"育肥期"）。
    """
    data = to_animal_out(a).model_dump()
    age_days = data.get("age_days")
    data["real_growth_stage"] = (
        determine_growth_stage(a.species, age_days) if age_days is not None else None
    )
    data["growth_stage"] = (
        "妊娠" if (a.growth_stage == "妊娠" or a.physio_status == "妊娠") else "繁育期"
    )
    return data


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
# 公畜健康档案（缺口4：健康状态/使用年限/配种记录）
# ============================================================

def list_males(
    db: Session, farm_id: int,
    species: Optional[str] = None, keyword: Optional[str] = None,
    page_num: int = 1, page_size: int = 10,
) -> dict:
    """公畜列表（档案基础信息 + 健康档案 + 配种统计）"""
    result = list_breed_animals(db, farm_id, "公", species, keyword, page_num=page_num, page_size=page_size)
    items = []
    for a in result["list"]:
        profile = db.query(BreedingMale).filter(
            BreedingMale.farm_id == farm_id, BreedingMale.ear_tag == a.ear_tag
        ).first()
        items.append(_male_out(db, a, profile))
    result["list"] = items
    return result


def update_male_health(db: Session, farm_id: int, ear_tag: str, body: MaleHealthIn) -> dict:
    """编辑公畜健康档案（不存在则创建；已淘汰公畜从可繁育列表剔除由档案状态控制）"""
    male = _get_animal(db, farm_id, ear_tag)
    if male.gender != "公":
        raise BizException(f"耳标 {ear_tag} 不是公畜，不能维护健康档案", code=40136)
    if body.health_status is not None and body.health_status not in MALE_HEALTH_STATUSES:
        raise BizException(f"健康状态只能是：{'/'.join(sorted(MALE_HEALTH_STATUSES))}", code=40137)

    profile = db.query(BreedingMale).filter(
        BreedingMale.farm_id == farm_id, BreedingMale.ear_tag == ear_tag
    ).first()
    if not profile:
        profile = BreedingMale(farm_id=farm_id, ear_tag=ear_tag)
        db.add(profile)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)
    # 未填启用日期时，用出生日期兜底
    if profile.use_start_date is None and male.birth_date:
        profile.use_start_date = male.birth_date
    db.commit()
    return _male_out(db, male, profile)


def _male_out(db: Session, a: Animal, profile: Optional[BreedingMale]) -> dict:
    """组装公畜返回：档案基础字段（含实时日龄/繁育口径阶段） + 健康档案 + 配种统计"""
    d = breed_animal_out(a)
    # 健康档案（无则默认健康，使用年限起点回退出生日期）
    health_status = profile.health_status if profile else "健康"
    use_start = profile.use_start_date if profile else a.birth_date
    d["health_status"] = health_status
    d["use_start_date"] = use_start
    d["semen_quality"] = profile.semen_quality if profile else None
    d["health_remark"] = profile.remark if profile else None
    # 使用年限（年，保留 1 位）
    if use_start:
        d["service_years"] = round((date.today() - use_start).days / 365.25, 1)
    else:
        d["service_years"] = None
    # 配种统计
    d["mating_count"] = db.query(MatingRecord).filter(
        MatingRecord.farm_id == a.farm_id, MatingRecord.male_tag == a.ear_tag,
        MatingRecord.deleted == False,
    ).count()
    d["success_count"] = db.query(MatingRecord).filter(
        MatingRecord.farm_id == a.farm_id, MatingRecord.male_tag == a.ear_tag,
        MatingRecord.status == "成功怀孕", MatingRecord.deleted == False,
    ).count()
    last = db.query(MatingRecord.mating_date).filter(
        MatingRecord.farm_id == a.farm_id, MatingRecord.male_tag == a.ear_tag,
        MatingRecord.deleted == False,
    ).order_by(MatingRecord.mating_date.desc()).first()
    d["last_mating_date"] = last[0] if last else None
    return d


def set_female_physio_status(db: Session, farm_id: int, female_tag: str, physio_status: str) -> Animal:
    """手动设置母畜生理状态（休情/淘汰等无自然触发的状态由场主/繁育员维护）"""
    if physio_status not in PHYSIO_STATUSES:
        raise BizException(f"生理状态只能是：{'/'.join(PHYSIO_STATUSES)}", code=40134)
    female = _get_animal(db, farm_id, female_tag)
    if female.gender != "母":
        raise BizException(f"耳标 {female_tag} 不是母畜，不能设置生理状态", code=40113)
    female.physio_status = physio_status
    # 与 growth_stage 妊娠标记保持一致，避免状态双轨漂移
    if physio_status == "妊娠" and female.growth_stage != "妊娠":
        female.growth_stage = "妊娠"
    elif physio_status != "妊娠" and female.growth_stage == "妊娠":
        female.growth_stage = "繁育期"
    db.commit()
    return female


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
    if query.audit_status:
        q = q.filter(MatingRecord.audit_status == query.audit_status)
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
    """
    新增配种记录：自动算预产期，进「待审核」。

    注意：这里**不再**动母畜档案 —— 审核通过（audit_mating）才把母畜置为"妊娠"。
    待审核/驳回的记录只是申请，母畜状态保持不变。
    """
    if body.species not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40111)
    if body.mating_type not in MATING_TYPES:
        raise BizException(f"配种方式只能是：{'/'.join(sorted(MATING_TYPES))}", code=40112)

    female = _get_animal(db, farm_id, body.female_tag)
    if female.gender != "母":
        raise BizException(f"耳标 {body.female_tag} 不是母畜，不能配种", code=40113)
    if female.growth_stage == "妊娠" or female.physio_status == "妊娠":
        raise BizException(f"母畜 {body.female_tag} 正处于妊娠状态，不能重复配种", code=40114)
    if female.physio_status == "淘汰":
        raise BizException(f"母畜 {body.female_tag} 已淘汰，不能配种", code=40135)
    # 同一母畜已有待审核的配种记录时不允许重复提交（避免审核通过后重复置妊娠）
    pending = db.query(MatingRecord).filter(
        MatingRecord.farm_id == farm_id,
        MatingRecord.female_tag == body.female_tag,
        MatingRecord.deleted == False,
        MatingRecord.audit_status == "待审核",
    ).first()
    if pending:
        raise BizException(
            f"母畜 {body.female_tag} 已有一条待审核的配种记录（ID:{pending.id}），请先等场主审核",
            code=40138,
        )

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
        audit_status="待审核",  # 提交固定进待审核，审核通过才生效
        expected_birth_date=expected_birth_date,
        gestation_days=gestation_days,
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(rec)
    db.commit()
    return rec


def audit_mating(db: Session, farm_id: int, record_id: int,
                 audit_status: str, remark: Optional[str] = None) -> MatingRecord:
    """
    审核配种记录（场主/超管）：
    - 通过：audit_status=通过，母畜置为"妊娠"（生长阶段 + 生理状态）
    - 驳回：audit_status=驳回，母畜档案不变
    """
    if audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40139)

    rec = get_mating(db, farm_id, record_id)
    if rec.audit_status != "待审核":
        raise BizException("该配种记录已审核，不能重复审核", code=40140)

    if audit_status == "通过":
        female = _get_animal(db, farm_id, rec.female_tag)
        # 防重复置妊娠：同母畜可能已有别的已通过记录
        if female.growth_stage == "妊娠" or female.physio_status == "妊娠":
            raise BizException(
                f"母畜 {rec.female_tag} 当前已是妊娠状态（可能另一条配种记录已审核通过），请先核实",
                code=40141,
            )
        female.growth_stage = "妊娠"
        female.physio_status = "妊娠"
        rec.status = "待孕检"

    rec.audit_status = audit_status
    if remark:
        rec.remark = remark
    db.commit()
    return rec


def update_mating(db: Session, farm_id: int, record_id: int, body: MatingUpdateIn) -> MatingRecord:
    """
    修改配种记录：改配种日期时重算预产期；已登记孕检的记录不允许改。

    已审核通过的记录也可以改，但改动后 audit_status 重置回「待审核」（同饲喂记录口径），
    并把该记录原先给母畜置的妊娠标记回退 —— 未重新审核通过前不生效。
    """
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

    was_approved = rec.audit_status == "通过"
    for k, v in data.items():
        setattr(rec, k, v)
    # 改配种日期 → 重算预产期（妊娠期不变）
    if data.get("mating_date"):
        rec.expected_birth_date = rec.mating_date + timedelta(days=rec.gestation_days or 0)
    if was_approved:
        rec.audit_status = "待审核"
        _restore_female_stage(db, farm_id, rec.female_tag)
    db.commit()
    return rec


def delete_mating(db: Session, farm_id: int, record_id: int):
    """
    删除配种记录：已关联产犊记录禁止删；已审核通过的不能删（同饲喂记录口径，
    如确需删除请先编辑该记录使其退回待审核）。
    """
    rec = get_mating(db, farm_id, record_id)
    linked = db.query(BirthRecord).filter(
        BirthRecord.mating_id == record_id, BirthRecord.deleted == False
    ).first()
    if linked:
        raise BizException("该配种记录已关联产犊记录，不能删除", code=40117)
    if rec.audit_status == "通过":
        raise BizException("已审核通过的配种记录不能删除，如需修改请先编辑（会退回待审核）", code=40142)
    rec.deleted = True
    db.commit()


def pregnancy_check(db: Session, farm_id: int, record_id: int, body: PregnancyCheckIn, user_id: int) -> MatingRecord:
    """孕检登记：阳性→成功怀孕；阴性→配种失败，母畜恢复繁育期（仅已审核通过的记录可登记）"""
    rec = get_mating(db, farm_id, record_id)
    if rec.audit_status != "通过":
        raise BizException("该配种记录尚未审核通过，不能登记孕检", code=40143)
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
        # 确保母畜生理状态保持妊娠（配种时已置位，防止被手动改动）
        female = _get_animal(db, farm_id, rec.female_tag)
        female.physio_status = "妊娠"
    else:
        rec.status = "配种失败"
        _restore_female_stage(db, farm_id, rec.female_tag)
    db.commit()
    return rec


def _restore_female_stage(db: Session, farm_id: int, female_tag: str) -> Optional[Animal]:
    """
    配种失败/删除配种/记录退回待审核后，母畜妊娠标记清除。
    生理状态回退为「正常」—— 「发情」只在母羊进入适配繁育周期时才代表真实状态，
    给牛/猪母畜统一置「发情」与实际生理不符（与档案模块的默认值规则保持一致）。
    """
    female = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.ear_tag == female_tag,
        Animal.deleted == False,
    ).first()
    if female:
        if female.growth_stage == "妊娠":
            female.growth_stage = "繁育期"
        if female.physio_status == "妊娠":
            female.physio_status = "正常"
    return female


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
        if mating.audit_status != "通过":
            raise BizException("关联的配种记录尚未审核通过，不能登记产犊", code=40144)

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
    # 产犊后母畜妊娠标记清除，生理状态进入泌乳
    female = _restore_female_stage(db, farm_id, body.female_tag)
    if female:
        female.physio_status = "泌乳"
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
# 繁育预警（列表接口按需生成 + 每日定时任务兜底，规则统一在 ensure_alerts）
# ============================================================

def _alert_exists(db: Session, farm_id: int, animal_tag: str,
                  alert_type: str, alert_date: date) -> bool:
    """同养殖场 + 同耳标 + 同类型 + 同预警日期已存在则视为已生成（幂等）"""
    return db.query(BreedingAlert).filter(
        BreedingAlert.farm_id == farm_id,
        BreedingAlert.animal_tag == animal_tag,
        BreedingAlert.alert_type == alert_type,
        BreedingAlert.alert_date == alert_date,
    ).first() is not None


def _notify_birth_alert(db: Session, farm_id: int, alert: BreedingAlert) -> None:
    """
    新建「临产」预警后，给本养殖场所有启用的场主推送站内消息（不 commit）。

    仅在 ensure_alerts 真正新建预警时调用，因此重复打开页面不会重复推送；
    send_message 在函数内导入，避免 breeding 与 system 模块之间形成顶层循环依赖。
    """
    from app.models.user import User
    from app.modules.system.service import send_message

    owners = db.query(User).filter(
        User.farm_id == farm_id,
        User.user_type == 2,  # 养殖场主
        User.status == 1,
        User.deleted == False,
    ).all()
    for owner in owners:
        send_message(
            db,
            farm_id=farm_id,
            receiver_user_id=owner.id,
            title=f"临产预警：耳标 {alert.animal_tag}",
            content=alert.alert_content,
            related_module="breeding",
            related_id=alert.id,
            message_type="系统提醒",
        )


def ensure_alerts(db: Session, farm_id: int) -> int:
    """
    按需生成指定养殖场的繁育预警（幂等），返回本次新建条数。

    规则（与每日 00:10 定时任务共用，只有这一份实现）：
    1. 孕检：已审核通过、状态「待孕检」、配种日期 <= 今天 - 60 天；
    2. 临产：已审核通过、状态「成功怀孕」、预产期非空且 <= 今天 + 15 天
       （不再限制 >= 今天，已过预产期的也要提醒，内容区分剩余/逾期）；
       新建临产预警时同步给本场场主发站内消息（顶栏铃铛未读角标）；
    3. 未发情：产犊已满 60 天，且产犊之后没有审核通过的配种记录。

    幂等键：farm_id + animal_tag + alert_type + alert_date（今天）。
    生成成功后内部提交；生成失败直接抛给调用方，由调用方 rollback 并决定是否影响主流程。
    """
    today = date.today()
    created = 0
    # 同一批次内同耳标同类型只生成一条（多胎次/多条历史配种记录时不重复）
    created_keys: set[tuple[str, str]] = set()

    def add_once(alert_type: str, animal_tag: str, related_id: Optional[int],
                 alert_content: str) -> None:
        nonlocal created
        key = (animal_tag, alert_type)
        if key in created_keys:
            return
        if _alert_exists(db, farm_id, animal_tag, alert_type, today):
            return
        # 同耳标同类型还有「待处理」的预警时不再重复生成：
        # 否则同一条临产提醒会在预产期前 15 天里每天堆一条，预警列表全是重复行、
        # 顶栏铃铛也会天天响。处理（已处理/已忽略）之后才会再生成新的提醒。
        already_pending = db.query(BreedingAlert.id).filter(
            BreedingAlert.farm_id == farm_id,
            BreedingAlert.animal_tag == animal_tag,
            BreedingAlert.alert_type == alert_type,
            BreedingAlert.status == "待处理",
            BreedingAlert.deleted == False,
        ).first()
        if already_pending:
            return
        rec = BreedingAlert(
            farm_id=farm_id,
            alert_type=alert_type,
            animal_tag=animal_tag,
            related_id=related_id,
            alert_date=today,
            alert_content=alert_content,
            status="待处理",
        )
        db.add(rec)
        db.flush()  # 先拿到预警 id，站内消息 related_id 需要
        created_keys.add(key)
        created += 1
        # 只有真正新建的临产预警才推送站内消息，重复调用不会重复发
        if alert_type == "临产":
            _notify_birth_alert(db, farm_id, rec)

    # 1. 孕检提醒：配种后满 60 天仍未孕检
    check_line = today - timedelta(days=PREGNANCY_CHECK_DAYS)
    matings = db.query(MatingRecord).filter(
        MatingRecord.farm_id == farm_id,
        MatingRecord.deleted == False,
        MatingRecord.audit_status == "通过",  # 未审核/驳回的记录不算数
        MatingRecord.status == "待孕检",
        MatingRecord.mating_date <= check_line,
    ).all()
    for m in matings:
        add_once(
            "孕检", m.female_tag, m.id,
            f"耳标 {m.female_tag} 配种已满 {PREGNANCY_CHECK_DAYS} 天，请尽快安排孕检（配种日期 {m.mating_date}）",
        )

    # 2. 临产提醒：预产期距今天 <= 15 天；已逾期同样提醒（此前 >= today 导致逾期个体永远不产生预警）
    remind_line = today + timedelta(days=BIRTH_REMIND_DAYS)
    pregnant = db.query(MatingRecord).filter(
        MatingRecord.farm_id == farm_id,
        MatingRecord.deleted == False,
        MatingRecord.audit_status == "通过",
        MatingRecord.status == "成功怀孕",
        MatingRecord.expected_birth_date.isnot(None),
        MatingRecord.expected_birth_date <= remind_line,
    ).all()
    for m in pregnant:
        remain = (m.expected_birth_date - today).days
        if remain >= 0:
            content = f"预产期 {m.expected_birth_date}，剩余 {remain} 天，请提前准备接产"
        else:
            content = f"预产期 {m.expected_birth_date}，已逾期 {abs(remain)} 天，请立即处理"
        add_once("临产", m.female_tag, m.id, content)

    # 3. 未发情提醒：产犊后满 60 天仍无下一次审核通过的配种记录
    heat_line = today - timedelta(days=HEAT_REMIND_DAYS)
    births = db.query(BirthRecord).filter(
        BirthRecord.farm_id == farm_id,
        BirthRecord.deleted == False,
        BirthRecord.birth_date <= heat_line,
    ).all()
    for b in births:
        later_mating = db.query(MatingRecord).filter(
            MatingRecord.farm_id == farm_id,
            MatingRecord.female_tag == b.female_tag,
            MatingRecord.deleted == False,
            MatingRecord.audit_status == "通过",
            MatingRecord.mating_date >= b.birth_date,
        ).first()
        if later_mating:
            continue
        add_once(
            "未发情", b.female_tag, b.id,
            f"耳标 {b.female_tag} 产犊已满 {HEAT_REMIND_DAYS} 天仍未配种，请关注发情情况（产犊日期 {b.birth_date}）",
        )

    db.commit()
    return created


def add_alert(db: Session, farm_id: int, body: AlertIn, user_id: int) -> BreedingAlert:
    """手动新增预警（仅补录/测试；自动生成走 ensure_alerts，暂不推送站内消息）"""
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
    if query.species:
        # 只返回该畜种动物的预警
        tags = db.query(Animal.ear_tag).filter(
            Animal.farm_id == farm_id, Animal.species == query.species, Animal.deleted == False
        ).all()
        tag_list = [r[0] for r in tags]
        q = q.filter(BreedingAlert.animal_tag.in_(tag_list) if tag_list else False)
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
