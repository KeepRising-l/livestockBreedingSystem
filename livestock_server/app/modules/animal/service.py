"""
档案业务逻辑

核心算法：
1. 耳标生成：前2位=圈舍编号（去掉字母前缀取数字部分），后2位=顺序号（复用空出的耳标）
2. 生长阶段判定：按出生日期 + 日龄区间 + 畜种判断
3. 圈舍自动分配：按生长阶段判定圈舍类型，找空位
4. 删除转历史：删除档案时转入 history 表，半年后自动清除
"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.utils import get_effective_farm_id
from app.modules.animal.model import Animal, AnimalHistory
from app.modules.animal.schema import (
    AnimalIndividualIn, AnimalBatchIn, AnimalImportIn, AnimalQuery,
    AnimalHistoryQuery, AnimalUpdateIn, AnimalOut,
)
from app.modules.pen.model import Pen
from app.modules.pen.service import (
    SPECIES_TAG_DIGIT,
    STAGE_TO_PEN_TYPE,
    claim_pen_species,
    ensure_pen_species_match,
    find_available_pen,
    list_available_pens,
    pen_tag_number,
)


# 各畜种生长阶段日龄配置
# 格式：(阶段名, 起始日龄, 结束日龄)
GROWTH_STAGE_CONFIG = {
    "牛": [
        ("犊牛期", 1, 60),
        ("保育期", 61, 180),
        ("生长期", 181, 365),
        ("育肥期", 366, 540),
    ],
    "羊": [
        ("羔羊期", 1, 45),
        ("保育期", 46, 90),
        ("生长期", 91, 180),
        ("育肥期", 181, 270),
    ],
    "猪": [
        ("仔猪期", 1, 28),
        ("保育期", 29, 70),
        ("生长期", 71, 120),
        ("育肥期", 121, 180),
    ],
}

# 可繁育起始日龄
BREEDABLE_AGE = {"牛": 365, "羊": 300, "猪": 220}
# 妊娠期天数
GESTATION_DAYS = {"牛": 280, "羊": 150, "猪": 114}
# 母畜生理状态（正常/发情/妊娠/泌乳/休情/淘汰），默认"正常"
PHYSIO_STATUSES = ("正常", "发情", "妊娠", "泌乳", "休情", "淘汰")


def calc_age_days(birth_date: date, ref_date: date = None) -> int:
    """计算日龄"""
    if not birth_date:
        return 0
    ref_date = ref_date or date.today()
    return (ref_date - birth_date).days


def determine_growth_stage(species: str, age_days: int) -> str:
    """
    根据畜种和日龄判定生长阶段
    优先级：妊娠期 > 其它阶段（妊娠期由配种记录单独标记，这里只算基础阶段）

    边界：日龄 < 1（今天出生或数据异常）按第一个阶段算，不再落到"繁育期"——
    旧实现区间从 1 开始，age=0 会穿透所有区间被误判为繁育期。
    """
    stages = GROWTH_STAGE_CONFIG.get(species)
    if not stages:
        raise BizException(f"不支持的畜种：{species}", code=40020)

    if age_days < stages[0][1]:
        return stages[0][0]
    for name, start, end in stages:
        if start <= age_days <= end:
            return name
    # 超过育肥期，按繁育期处理
    return "繁育期"


def default_physio_status(species: str, gender: str, age_days: int) -> Optional[str]:
    """
    入栏时母畜的默认生理状态：
    - 默认"正常"（旧实现全部默认"发情"，与实际生理不符）
    - 仅当母羊进入适配繁育周期（日龄 >= 可繁育起始日龄）时才默认"发情"
    - 公畜不跟踪生理状态，返回 None
    """
    if gender != "母":
        return None
    if species == "羊" and age_days >= BREEDABLE_AGE["羊"]:
        return "发情"
    return "正常"


def parse_ear_tag_prefix(pen: Pen, species_override: str = None) -> str:
    """
    生成耳标前缀（3 位）= 畜种位 + 圈舍编号数字（2 位）

    例：牛/A02 -> 1 + 02 = "102"，该圈舍第 7 头入栏 -> 耳标 "10207"

    为什么带畜种位：圈舍编号只在畜种内唯一（牛和羊都可以有 A02），
    只用编号数字的话跨畜种会撞号。
    编号数字在同一畜种内由 pen.service.ensure_pen_tag_number_unique 保证唯一，
    因此这个前缀在养殖场内全局唯一。

    species_override：圈舍尚未分配畜种时，用调用方传入的畜种来预览
    """
    species = species_override or pen.species
    if not species:
        raise BizException(
            f"圈舍 {pen.pen_code} 尚未分配畜种，无法生成耳标（请先在圈舍管理里指定畜种）",
            code=40021,
        )
    digit = SPECIES_TAG_DIGIT.get(species)
    if not digit:
        raise BizException(f"未知畜种：{species}", code=40021)
    number = pen_tag_number(pen.pen_code)
    if not number:
        raise BizException(
            f"圈舍编号 {pen.pen_code} 里没有数字，无法生成耳标", code=40021
        )
    return digit + number


def generate_ear_tag(db: Session, farm_id: int, pen: Pen, species_override: str = None) -> str:
    fid = get_effective_farm_id(db, farm_id)
    """
    生成耳标（5 位）：前3位=畜种位+圈舍编号数字，后2位=入栏序号（自动复用空出的号）

    算法：
    1. 找出该圈舍所有已用耳标的后 2 位
    2. 从 01 开始找第一个未使用的号
    3. 同时考虑已删除档案释放的耳标号
    """
    prefix = parse_ear_tag_prefix(pen, species_override)

    # 统计该圈舍当前在用的序号：按耳标后 2 位算，
    # 这样即使圈里还留着旧规则（4 位）的耳标，序号也不会被重复发出
    used_suffixes = set()
    animals = db.query(Animal).filter(
        Animal.farm_id == fid,
        Animal.pen_id == pen.id,
        Animal.deleted == False,
        Animal.status.in_(["在栏", "种用", "隔离", "待出栏"]),
    ).all()
    for a in animals:
        if a.ear_tag and len(a.ear_tag) >= 4:
            used_suffixes.add(a.ear_tag[-2:])

    # 从 01 到 capacity 找第一个空号
    for i in range(1, 100):
        suffix = str(i).zfill(2)
        if suffix not in used_suffixes:
            return prefix + suffix

    raise BizException(f"圈舍 {pen.pen_code} 耳标号已用尽", code=40022)


def to_animal_out(a: Animal) -> AnimalOut:
    """
    ORM -> DTO，同时按出生日期实时回填日龄和生长阶段：
    - age_days = 今天 - 出生日期（无出生日期为 None）
    - growth_stage 实时按日龄重算（存储值由每日 00:05 调度任务兜底刷新，
      breeding 模块依赖存储值做繁育期筛选，因此 DB 字段保留）；
      例外：存储值为"妊娠"时保留——妊娠期由配种记录标记，不能按日龄覆盖
    """
    out = AnimalOut.model_validate(a)
    if not a.birth_date:
        return out
    age_days = calc_age_days(a.birth_date)
    stage = a.growth_stage if a.growth_stage == "妊娠" else determine_growth_stage(a.species, age_days)
    return out.model_copy(update={"age_days": age_days, "growth_stage": stage})


def list_animals(db: Session, farm_id: int, query: AnimalQuery) -> dict:
    """档案列表，支持多条件筛选"""
    fid = get_effective_farm_id(db, farm_id)
    q = db.query(Animal).filter(Animal.farm_id == fid, Animal.deleted == False)
    if query.ear_tag:
        q = q.filter(Animal.ear_tag.like(f"%{query.ear_tag}%"))
    if query.species:
        q = q.filter(Animal.species == query.species)
    if query.pen_id:
        q = q.filter(Animal.pen_id == query.pen_id)
    if query.breed:
        q = q.filter(Animal.breed == query.breed)
    if query.gender:
        q = q.filter(Animal.gender == query.gender)
    if query.status:
        q = q.filter(Animal.status == query.status)
    if query.physio_status:
        q = q.filter(Animal.physio_status == query.physio_status)

    total = q.count()
    items = q.order_by(Animal.ear_tag).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def list_animals_grouped(
    db: Session, farm_id: int, query: AnimalQuery, pageNum: int = 1, pageSize: int = 10,
) -> dict:
    """
    档案分级展示：按圈舍分组，每组带汇总（存栏数/公母/品种构成/平均日龄），
    组内为该圈舍全部个体明细（已应用搜索筛选）。

    分页以圈舍为单位；"无圈舍"（pen_id 为 NULL 的个体）单独成组排在最后。
    """
    fid = get_effective_farm_id(db, farm_id)
    q = db.query(Animal).filter(Animal.farm_id == fid, Animal.deleted == False)
    if query.ear_tag:
        q = q.filter(Animal.ear_tag.like(f"%{query.ear_tag}%"))
    if query.species:
        q = q.filter(Animal.species == query.species)
    if query.breed:
        q = q.filter(Animal.breed == query.breed)
    if query.gender:
        q = q.filter(Animal.gender == query.gender)
    if query.status:
        q = q.filter(Animal.status == query.status)
    if query.physio_status:
        q = q.filter(Animal.physio_status == query.physio_status)
    animals = q.order_by(Animal.ear_tag).all()

    # 查涉及的圈舍
    pen_ids = {a.pen_id for a in animals if a.pen_id}
    pens = {
        p.id: p for p in db.query(Pen).filter(Pen.id.in_(pen_ids)).all()
    } if pen_ids else {}

    # 分组汇总
    groups: dict[int | None, dict] = {}
    for a in animals:
        g = groups.setdefault(a.pen_id, {
            "pen_id": a.pen_id,
            "pen_code": None,
            "pen_type": None,
            "capacity": None,
            "current_count": None,
            "count": 0,
            "male_count": 0,
            "female_count": 0,
            "breed_map": {},
            "age_sum": 0,
            "age_known": 0,
            "animals": [],
        })
        g["count"] += 1
        if a.gender == "公":
            g["male_count"] += 1
        elif a.gender == "母":
            g["female_count"] += 1
        g["breed_map"][a.breed] = g["breed_map"].get(a.breed, 0) + 1
        if a.birth_date:
            g["age_sum"] += calc_age_days(a.birth_date)
            g["age_known"] += 1
        g["animals"].append(a)

    # 组排序：有圈舍的按编号排，无圈舍的排最后
    def sort_key(item):
        pen_id, g = item
        if pen_id is None or pen_id not in pens:
            return (1, "")
        return (0, pens[pen_id].pen_code or "")

    ordered = [g for _, g in sorted(groups.items(), key=sort_key)]

    total = len(ordered)
    page_items = ordered[(pageNum - 1) * pageSize: pageNum * pageSize]

    result = []
    for g in page_items:
        pen = pens.get(g["pen_id"])
        if pen:
            g["pen_code"] = pen.pen_code
            g["pen_type"] = pen.pen_type
            g["capacity"] = pen.capacity
            g["current_count"] = pen.current_count
        g["breeds"] = [
            {"breed": b, "count": c}
            for b, c in sorted(g["breed_map"].items(), key=lambda x: -x[1])
        ]
        g["avg_age_days"] = round(g["age_sum"] / g["age_known"]) if g["age_known"] else None
        g["animals"] = [to_animal_out(a) for a in g["animals"]]
        del g["breed_map"], g["age_sum"], g["age_known"]
        result.append(g)

    return {"list": result, "total": total, "pageNum": pageNum, "pageSize": pageSize,
            "animal_total": len(animals)}


def get_animal(db: Session, farm_id: int, animal_id: int) -> Animal:
    fid = get_effective_farm_id(db, farm_id)
    a = db.query(Animal).filter(
        Animal.id == animal_id, Animal.farm_id == fid, Animal.deleted == False
    ).first()
    if not a:
        raise BizException("档案不存在", code=40023)
    return a


def update_animal(db: Session, farm_id: int, animal_id: int, body: AnimalUpdateIn) -> Animal:
    """
    修改档案（仅更新传入字段）：
    - pen_id 变更：校验新圈舍容量 → 旧圈舍存栏-1 / 新圈舍存栏+1 → 重新生成耳标
    - birth_date 或 species 变更：重算生长阶段
    """
    fid = get_effective_farm_id(db, farm_id)
    a = get_animal(db, fid, animal_id)

    # 处理圈舍变更
    if body.pen_id is not None and body.pen_id != a.pen_id:
        new_pen = db.query(Pen).filter(
            Pen.id == body.pen_id, Pen.farm_id == fid, Pen.deleted == False
        ).first()
        if not new_pen:
            raise BizException("目标圈舍不存在", code=40029)
        if (new_pen.current_count or 0) >= new_pen.capacity:
            raise BizException(
                f"目标圈舍 {new_pen.pen_code} 已满（{new_pen.current_count}/{new_pen.capacity}）",
                code=40030,
            )
        # 目标圈舍的畜种归属必须与该畜禽一致（未归属的圈舍随本次转舍自动归属）
        target_species = body.species if body.species is not None else a.species
        ensure_pen_species_match(new_pen, target_species)
        claim_pen_species(new_pen, target_species)
        # 旧圈舍存栏-1
        if a.pen_id:
            old_pen = db.query(Pen).filter(Pen.id == a.pen_id).first()
            if old_pen and (old_pen.current_count or 0) > 0:
                old_pen.current_count -= 1
        # 生成新耳标
        new_ear_tag = generate_ear_tag(db, fid, new_pen)
        # 校验耳标唯一（排除自身）
        conflict = db.query(Animal).filter(
            Animal.farm_id == fid, Animal.ear_tag == new_ear_tag,
            Animal.deleted == False, Animal.id != a.id,
        ).first()
        if conflict:
            raise BizException(f"耳标 {new_ear_tag} 已存在", code=40031)
        a.pen_id = new_pen.id
        a.ear_tag = new_ear_tag
        new_pen.current_count = (new_pen.current_count or 0) + 1

    # 处理出生日期/畜种变更 → 重算生长阶段
    if body.birth_date is not None or body.species is not None:
        species = body.species if body.species is not None else a.species
        birth_date = body.birth_date if body.birth_date is not None else a.birth_date
        age_days = calc_age_days(birth_date, a.in_date or date.today())
        a.growth_stage = determine_growth_stage(species, age_days)

    # 更新普通字段
    if body.breed is not None:
        a.breed = body.breed
    if body.species is not None:
        a.species = body.species
    if body.gender is not None:
        a.gender = body.gender
    if body.in_date is not None:
        a.in_date = body.in_date
    if body.status is not None:
        a.status = body.status
    if body.physio_status is not None:
        if body.physio_status not in PHYSIO_STATUSES:
            raise BizException(
                f"生理状态只能是：{'/'.join(PHYSIO_STATUSES)}",
                code=40032,
            )
        a.physio_status = body.physio_status
    if body.source is not None:
        a.source = body.source
    if body.sire_tag is not None:
        a.sire_tag = body.sire_tag
    if body.dam_tag is not None:
        a.dam_tag = body.dam_tag
    if body.remark is not None:
        a.remark = body.remark

    db.commit()
    return a


def transfer_animal(db: Session, farm_id: int, animal_id: int, target_pen_id: int) -> Animal:
    """转入其他圈舍（缺口5）：复用 update_animal 圈舍变更逻辑（容量校验/存栏联动/耳标重生）"""
    return update_animal(db, farm_id, animal_id, AnimalUpdateIn(pen_id=target_pen_id))


def remove_from_pen(db: Session, farm_id: int, animal_id: int) -> Animal:
    """移出圈舍（缺口5）：旧圈舍存栏-1，pen_id 置空；耳标保留，重新入舍时自动重生"""
    fid = get_effective_farm_id(db, farm_id)
    a = get_animal(db, fid, animal_id)
    if not a.pen_id:
        raise BizException("该档案当前不在圈舍中", code=40033)
    old_pen = db.query(Pen).filter(Pen.id == a.pen_id).first()
    if old_pen and (old_pen.current_count or 0) > 0:
        old_pen.current_count -= 1
    a.pen_id = None
    db.commit()
    return a


def individual_create(db: Session, farm_id: int, body: AnimalIndividualIn) -> Animal:
    fid = get_effective_farm_id(db, farm_id)
    """个体入栏"""
    # 1. 确定圈舍：传了 pen_id 就用，没传就按生长阶段自动分配
    if body.pen_id:
        pen = db.query(Pen).filter(
            Pen.id == body.pen_id, Pen.farm_id == fid, Pen.deleted == False
        ).first()
        if not pen:
            raise BizException("指定圈舍不存在", code=40024)
        if pen.current_count >= pen.capacity:
            raise BizException("指定圈舍已满", code=40025)
        # 圈舍已归属其它畜种时拒绝入栏，避免牛舍里混进羊
        ensure_pen_species_match(pen, body.species)
    else:
        # 根据出生日期算日龄，再算生长阶段，再算圈舍类型
        age_days = calc_age_days(body.birth_date, body.in_date or date.today())
        stage = determine_growth_stage(body.species, age_days)
        pen_type = STAGE_TO_PEN_TYPE.get(stage, "A")
        # 自动分配时同样只在本畜种的圈舍里挑
        pen = find_available_pen(db, fid, pen_type, body.species)

    # 圈舍尚未归属畜种时，随本次入栏自动归属
    claim_pen_species(pen, body.species)

    # 2. 生成耳标
    ear_tag = generate_ear_tag(db, fid, pen)

    # 3. 校验耳标唯一
    exists = db.query(Animal).filter(
        Animal.farm_id == fid, Animal.ear_tag == ear_tag, Animal.deleted == False
    ).first()
    if exists:
        raise BizException(f"耳标 {ear_tag} 已存在", code=40026)

    # 4. 计算生长阶段
    age_days = calc_age_days(body.birth_date, body.in_date or date.today())
    stage = determine_growth_stage(body.species, age_days)

    # 5. 创建档案
    animal = Animal(
        farm_id=fid,
        ear_tag=ear_tag,
        species=body.species,
        breed=body.breed,
        pen_id=pen.id,
        gender=body.gender,
        birth_date=body.birth_date,
        in_date=body.in_date or date.today(),
        growth_stage=stage,
        physio_status=default_physio_status(body.species, body.gender, age_days),
        status=body.status,
        source=body.source,
        sire_tag=body.sire_tag,
        dam_tag=body.dam_tag,
        remark=body.remark,
    )
    db.add(animal)
    # 6. 更新圈舍存栏数
    pen.current_count = (pen.current_count or 0) + 1
    db.commit()
    return animal


def batch_create(db: Session, farm_id: int, body: AnimalBatchIn) -> dict:
    fid = get_effective_farm_id(db, farm_id)
    """
    批量入栏
    返回分配方案：每个圈舍分配了多少只、耳标范围
    """
    # 先算单只的阶段和圈舍类型
    age_days = calc_age_days(body.birth_date, body.in_date or date.today())
    stage = determine_growth_stage(body.species, age_days)
    pen_type = STAGE_TO_PEN_TYPE.get(stage, "A")

    # 找出本畜种下所有可用圈舍（按编号排序）
    pens = list_available_pens(db, fid, pen_type, body.species)

    # 计算总空位数
    total_avail = sum(p.capacity - p.current_count for p in pens)
    if total_avail < body.count:
        raise BizException(
            f"{body.species}在类型 {pen_type} 圈舍的空位不足，需要 {body.count}，可用 {total_avail}",
            code=40027,
        )

    # 依次分配
    plan = []  # 分配方案
    remain = body.count
    created = []

    for pen in pens:
        if remain <= 0:
            break
        # 圈舍尚未归属畜种时，随本次批量入栏自动归属
        claim_pen_species(pen, body.species)
        slot = min(remain, pen.capacity - pen.current_count)
        # 为这个圈舍生成 slot 个耳标
        ear_tags = []
        for _ in range(slot):
            et = generate_ear_tag(db, fid, pen)
            animal = Animal(
                farm_id=fid,
                ear_tag=et,
                species=body.species,
                breed=body.breed,
                pen_id=pen.id,
                gender=body.gender,
                birth_date=body.birth_date,
                in_date=body.in_date or date.today(),
                growth_stage=stage,
                physio_status=default_physio_status(body.species, body.gender, age_days),
                status=body.status,
                source=body.source,
                remark=body.remark,
            )
            db.add(animal)
            db.flush()  # 拿到 id，但不提交
            ear_tags.append(et)
            pen.current_count = (pen.current_count or 0) + 1
        plan.append({
            "pen_id": pen.id,
            "pen_code": pen.pen_code,
            "count": slot,
            "ear_tags": ear_tags,
        })
        remain -= slot

    db.commit()
    return {
        "total": body.count,
        "stage": stage,
        "pen_type": pen_type,
        "plan": plan,
    }


def import_create(db: Session, farm_id: int, body: AnimalImportIn) -> dict:
    """
    Excel 批量导入：逐行复用 individual_create（自动分配圈舍 + 生成耳标）
    跳过坏行、部分成功：单行失败 rollback 后继续下一行
    """
    fid = get_effective_farm_id(db, farm_id)
    results = []
    for i, row in enumerate(body.rows, start=1):
        # 基础字段校验（逐行跳过，不中断）
        if not row.breed.strip():
            results.append({"row": i, "ok": False, "ear_tag": None, "breed": row.breed, "gender": row.gender, "error": "品种不能为空"})
            continue
        if row.gender not in ("公", "母"):
            results.append({"row": i, "ok": False, "ear_tag": None, "breed": row.breed, "gender": row.gender, "error": "性别须为 公/母"})
            continue
        # 出生日期必填：禁止留空/跳过，系统据此自动推算日龄和生长阶段
        if not row.birth_date:
            results.append({"row": i, "ok": False, "ear_tag": None, "breed": row.breed, "gender": row.gender, "error": "出生日期必填（用于自动计算日龄和生长阶段）"})
            continue
        if row.birth_date > date.today():
            results.append({"row": i, "ok": False, "ear_tag": None, "breed": row.breed, "gender": row.gender, "error": "出生日期不能晚于今天"})
            continue
        try:
            a = individual_create(db, fid, AnimalIndividualIn(
                species=body.species,
                breed=row.breed,
                gender=row.gender,
                birth_date=row.birth_date,
                in_date=row.in_date,
                source=row.source,
                remark=row.remark,
            ))
            results.append({
                "row": i,
                "ok": True,
                "ear_tag": a.ear_tag,
                "breed": a.breed,
                "gender": a.gender,
                "error": None,
            })
        except BizException as e:
            db.rollback()
            results.append({
                "row": i,
                "ok": False,
                "ear_tag": None,
                "breed": row.breed,
                "gender": row.gender,
                "error": str(e),
            })

    success = sum(1 for r in results if r["ok"])
    return {
        "total": len(results),
        "success": success,
        "failed": len(results) - success,
        "results": results,
    }


def batch_delete(db: Session, farm_id: int, ids: list[int]):
    """批量删除：转入历史记录表"""
    fid = get_effective_farm_id(db, farm_id)
    today = date.today()
    clean_deadline = today + timedelta(days=180)  # 半年后清除

    for animal_id in ids:
        a = get_animal(db, fid, animal_id)
        # 转入历史
        history = AnimalHistory(
            farm_id=a.farm_id,
            ear_tag=a.ear_tag,
            species=a.species,
            breed=a.breed,
            pen_id=a.pen_id,
            gender=a.gender,
            birth_date=a.birth_date,
            in_date=a.in_date,
            out_date=a.out_date,
            growth_stage=a.growth_stage,
            physio_status=a.physio_status,
            status=a.status,
            source=a.source,
            sire_tag=a.sire_tag,
            dam_tag=a.dam_tag,
            remark=a.remark,
            delete_time=today,
        )
        db.add(history)
        # 逻辑删除档案
        a.deleted = True
        # 圈舍存栏数减1
        if a.pen_id:
            pen = db.query(Pen).filter(Pen.id == a.pen_id).first()
            if pen and pen.current_count > 0:
                pen.current_count -= 1

    db.commit()
    return {"deleted": len(ids)}


def list_history(db: Session, farm_id: int, query: AnimalHistoryQuery) -> dict:
    """历史记录列表，支持多条件筛选"""
    fid = get_effective_farm_id(db, farm_id)
    q = db.query(AnimalHistory).filter(
        AnimalHistory.farm_id == fid, AnimalHistory.deleted == False
    )
    if query.ear_tag:
        q = q.filter(AnimalHistory.ear_tag.like(f"%{query.ear_tag}%"))
    if query.species:
        q = q.filter(AnimalHistory.species == query.species)
    if query.breed:
        q = q.filter(AnimalHistory.breed == query.breed)
    if query.gender:
        q = q.filter(AnimalHistory.gender == query.gender)
    if query.status:
        q = q.filter(AnimalHistory.status == query.status)

    total = q.count()
    items = q.order_by(AnimalHistory.delete_time.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def restore_animal(db: Session, farm_id: int, history_id: int) -> Animal:
    """
    恢复已删除的档案：
    1. 校验历史记录存在
    2. 校验原档案记录还在（逻辑删除未物理清除）
    3. 校验耳标未被新档案占用（同圈舍+同耳标+未删除）
    4. 校验原圈舍容量是否充足
    5. 恢复原档案 deleted=False + 圈舍存栏+1 + 历史记录逻辑删除
    """
    fid = get_effective_farm_id(db, farm_id)
    h = db.query(AnimalHistory).filter(
        AnimalHistory.id == history_id, AnimalHistory.farm_id == fid, AnimalHistory.deleted == False
    ).first()
    if not h:
        raise BizException("历史记录不存在或已恢复", code=40024)

    # 找到原档案（同 ear_tag + 同 farm_id 的逻辑删除记录）
    animal = db.query(Animal).filter(
        Animal.farm_id == fid,
        Animal.ear_tag == h.ear_tag,
        Animal.deleted == True,
    ).first()
    if not animal:
        raise BizException("原档案记录已被清除，无法恢复", code=40025)

    # 校验耳标是否已被新档案占用（同圈舍+同耳标+未删除）
    conflict = db.query(Animal).filter(
        Animal.farm_id == fid,
        Animal.pen_id == animal.pen_id,
        Animal.ear_tag == h.ear_tag,
        Animal.deleted == False,
    ).first()
    if conflict:
        raise BizException(
            f"耳标 {h.ear_tag} 已被该圈舍其他档案占用，请先处理冲突",
            code=40026,
        )

    # 校验原圈舍是否还存在且容量充足
    if animal.pen_id:
        pen = db.query(Pen).filter(Pen.id == animal.pen_id, Pen.deleted == False).first()
        if not pen:
            raise BizException("原所在圈舍已被删除，无法恢复", code=40027)
        if (pen.current_count or 0) >= pen.capacity:
            raise BizException(
                f"原圈舍 {pen.pen_code} 已满（当前 {pen.current_count}/{pen.capacity}），无法恢复",
                code=40028,
            )
        pen.current_count = (pen.current_count or 0) + 1

    # 恢复档案
    animal.deleted = False
    # 历史记录逻辑删除
    h.deleted = True
    db.commit()
    return animal
