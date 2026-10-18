"""
圈舍业务逻辑

畜种归属（species）
- 圈舍明确归属一个畜种：牛/羊/猪，列表按该字段区分（原先靠"圈里有没有该畜种动物"反推，
  导致新建的空圈舍在三个畜种列表里都查不到）
- 历史数据里 species 为 NULL 的圈舍视为「待归属」：仍在列表中可见并标记，
  首次入栏时自动归属，也可在编辑弹窗里手动指定

核心算法：圈舍自动分配
- 根据生长阶段判定应入哪类圈舍（A/B/C/D）
- 在该类型 + 该畜种下找有空位的圈舍，按编号排序，依次分配
"""
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.utils import get_effective_farm_id
from app.modules.pen.model import Pen
from app.modules.pen.schema import PenAddIn, PenBatchAddIn, PenUpdateIn


# 生长阶段 -> 圈舍类型映射
STAGE_TO_PEN_TYPE = {
    "犊牛期": "A", "羔羊期": "A", "仔猪期": "A",
    "保育期": "A",
    "生长期": "B",
    "育肥期": "B",
    "繁育期": "C",
    "妊娠期": "C",
    "种用": "D",
}

# 圈舍类型默认容量
DEFAULT_CAPACITY = {
    "A": 12,
    "B": 12,
    "C": 6,
    "D": 1,
}

# 合法畜种
SPECIES_ALLOWED = ("牛", "羊", "猪")

# 耳标里的畜种位：牛=1 / 羊=2 / 猪=3（耳标共 5 位：畜种位 + 圈舍编号数字2位 + 序号2位）
SPECIES_TAG_DIGIT = {"牛": "1", "羊": "2", "猪": "3"}

# 批量添加单次数量上限
BATCH_MAX_COUNT = 50
# 编号格式：字母前缀 + 数字序号（如 A01；也允许 A1、A001 这类手工写法）
PEN_CODE_PATTERN = re.compile(r"^[A-Za-z]+\d{1,6}$")
# 编号前缀：纯字母
PEN_CODE_PREFIX_PATTERN = re.compile(r"^[A-Za-z]{1,10}$")


def validate_species(species: str, code: int = 40016):
    """校验畜种取值；None / 空串表示"待归属"，放行"""
    if species and species not in SPECIES_ALLOWED:
        raise BizException(f"畜种只能是：{'/'.join(SPECIES_ALLOWED)}", code=code)


def validate_pen_type(pen_type: str):
    """校验圈舍类型；单条新增与批量新增共用同一份规则"""
    if pen_type not in ("A", "B", "C", "D"):
        raise BizException("圈舍类型必须是 A/B/C/D", code=40011)


def pen_tag_number(pen_code: str) -> str:
    """
    取圈舍编号里的数字部分，作为耳标中的「圈舍号」（2 位）
    A02 -> 02、A2 -> 02、D10 -> 10
    没有数字则返回空串（由调用方决定报错）
    """
    if not pen_code:
        return ""
    digits = "".join(c for c in pen_code if c.isdigit())
    if not digits:
        return ""
    return digits.zfill(2)[-2:]


def ensure_pen_tag_number_unique(db: Session, farm_id: int, pen_code: str, species: str,
                                 exclude_id: int = None):
    """
    耳标前 3 位 = 畜种位 + 圈舍编号数字，所以「同一畜种内编号的数字部分不能重复」，
    否则两个圈舍会发出同样的耳标（例如牛/A01 与牛/B01 数字都是 01）。
    """
    num = pen_tag_number(pen_code)
    if not num:
        raise BizException(
            f"圈舍编号 {pen_code} 里没有数字，无法生成耳标（耳标需要编号中的 2 位数字）",
            code=40021,
        )
    query = db.query(Pen).filter(
        Pen.farm_id == farm_id, Pen.deleted == False
    ).filter(_pen_code_scope_filter(species))
    if exclude_id:
        query = query.filter(Pen.id != exclude_id)
    for other in query.all():
        if pen_tag_number(other.pen_code) == num:
            raise BizException(
                f"{_pen_code_scope_label(species)}圈舍编号 {pen_code} 的数字部分是 {num}，"
                f"与已有圈舍 {other.pen_code} 重复 —— 两者会发出相同耳标，请换一个编号",
                code=40022,
            )


def ensure_pen_species_match(pen: Pen, species: str):
    """
    校验圈舍与该畜种是否相容：
    - 圈舍未归属（NULL）：相容，调用方随后可用 claim_pen_species 自动归属
    - 圈舍已归属同一畜种：相容
    - 圈舍已归属其它畜种：拒绝，避免把羊放进牛舍
    """
    if not species or not pen or not pen.species:
        return
    if pen.species != species:
        raise BizException(
            f"圈舍 {pen.pen_code} 已归属「{pen.species}」，不能放入「{species}」",
            code=40018,
        )


def claim_pen_species(pen: Pen, species: str):
    """首次入栏时，把尚未归属的圈舍自动归属到该畜种"""
    if species and pen is not None and not pen.species:
        pen.species = species


def list_pens(db: Session, farm_id: int, pen_type: str = None, species: str = None,
              status: int = None, page_num: int = 1, page_size: int = 10) -> dict:
    """圈舍列表：按圈舍自身的畜种归属过滤"""
    fid = get_effective_farm_id(db, farm_id)
    query = db.query(Pen).filter(Pen.farm_id == fid, Pen.deleted == False)
    if pen_type:
        query = query.filter(Pen.pen_type == pen_type)
    if species:
        # 只返回该畜种的圈舍；species 为 NULL 的「待归属」圈舍保留可见，
        # 否则历史数据（以及异常情况下未写畜种的圈舍）会从列表里凭空消失、无法再被指派
        query = query.filter(or_(Pen.species == species, Pen.species.is_(None)))
    if status is not None:
        query = query.filter(Pen.status == status)
    total = query.count()
    items = query.order_by(Pen.pen_code).offset((page_num - 1) * page_size).limit(page_size).all()
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def get_pen(db: Session, farm_id: int, pen_id: int) -> Pen:
    fid = get_effective_farm_id(db, farm_id)
    pen = db.query(Pen).filter(
        Pen.id == pen_id, Pen.farm_id == fid, Pen.deleted == False
    ).first()
    if not pen:
        raise BizException("圈舍不存在", code=40010)
    return pen


def _pen_code_scope_filter(species: str):
    """圈舍编号的查重范围：按畜种各自独立编号，牛/羊/猪 都可以有自己的 A01。
    species 为 NULL（待归属）的圈舍自成一组。"""
    return Pen.species.is_(None) if species is None else Pen.species == species


def _pen_code_scope_label(species: str) -> str:
    return f"「{species}」" if species else "未分配畜种的"


def add_pen(db: Session, farm_id: int, body: PenAddIn) -> Pen:
    """新增圈舍"""
    fid = get_effective_farm_id(db, farm_id)
    validate_pen_type(body.pen_type)
    species = (body.species or "").strip() or None
    validate_species(species)
    code = (body.pen_code or "").strip()
    if not code:
        raise BizException("圈舍编号不能为空", code=40012)
    # 编号在本畜种内唯一：牛的 A01 与羊的 A01 可以并存
    dup = db.query(Pen).filter(
        Pen.farm_id == fid, Pen.pen_code == code, Pen.deleted == False
    ).filter(_pen_code_scope_filter(species)).first()
    if dup:
        raise BizException(
            f"{_pen_code_scope_label(species)}圈舍编号 {code} 已存在", code=40012
        )
    # 耳标前 3 位 = 畜种位 + 编号数字 → 同畜种内编号的数字部分必须唯一
    ensure_pen_tag_number_unique(db, fid, code, species)
    pen = Pen(
        farm_id=fid,
        pen_code=code,
        pen_type=body.pen_type,
        species=species,
        capacity=body.capacity,
        current_count=0,
        status=1,
        remark=body.remark,
    )
    db.add(pen)
    db.commit()
    return pen


def _batch_code_format_error(code: str) -> str:
    """批量添加的编号格式校验，返回错误文案；空串表示通过"""
    if not code:
        return "圈舍编号不能为空"
    if len(code) > 20:
        return "圈舍编号不能超过 20 个字符"
    if not PEN_CODE_PATTERN.match(code):
        return "圈舍编号格式应为「字母前缀 + 数字序号」，如 A01"
    return ""


def generate_batch_codes(prefix: str, start_no: int, count: int) -> list[str]:
    """按「前缀 + 起始序号 + 数量」生成编号，序号统一补 2 位：A/1/12 -> A01~A12"""
    return [f"{prefix}{start_no + i:02d}" for i in range(count)]


def _resolve_batch_codes(body: PenBatchAddIn) -> list[str]:
    """
    确定本次要创建的编号列表：
    - 传了 codes 就直接用（前端预览后允许用户手工调整，以用户编辑结果为准）
    - 否则按 prefix + start_no + count 由服务端生成
    """
    codes = [c.strip() for c in (body.codes or []) if c and c.strip()]
    if codes:
        if len(codes) > BATCH_MAX_COUNT:
            raise BizException(
                f"批量添加最多 {BATCH_MAX_COUNT} 条，本次提交 {len(codes)} 条", code=40023
            )
        return codes

    if body.prefix is None or body.start_no is None or body.count is None:
        raise BizException("请提供圈舍编号列表，或提供编号前缀、起始序号和数量", code=40024)
    prefix = (body.prefix or "").strip()
    if not PEN_CODE_PREFIX_PATTERN.match(prefix):
        raise BizException("编号前缀只能是 1~10 位字母，如 A", code=40025)
    if body.start_no < 1 or body.start_no > 999999:
        raise BizException("起始序号必须在 1~999999 之间", code=40024)
    if body.count < 1 or body.count > BATCH_MAX_COUNT:
        raise BizException(f"批量数量必须在 1~{BATCH_MAX_COUNT} 之间", code=40023)
    return generate_batch_codes(prefix, body.start_no, body.count)


def batch_add_pens(db: Session, farm_id: int, body: PenBatchAddIn) -> dict:
    """
    批量新增圈舍：逐条复用 add_pen 的校验与落库逻辑，不复制一份规则。

    - 公共字段（畜种 / 类型 / 容量）先整体校验，参数错了直接报业务错误
    - 编号逐条校验格式、同畜种内重复、耳标数字冲突：不合法的跳过并记录原因，
      不影响其它编号，从而支持「成功 N 条，跳过 M 条」
    - add_pen 内部按条提交；单条失败后回滚，避免脏会话影响后续编号
    """
    fid = get_effective_farm_id(db, farm_id)
    validate_pen_type(body.pen_type)
    species = (body.species or "").strip() or None
    validate_species(species)
    if body.capacity is None or body.capacity < 1:
        raise BizException("容量必须大于 0", code=40026)
    codes = _resolve_batch_codes(body)

    created_codes: list[str] = []
    skipped: list[dict] = []
    for code in codes:
        reason = _batch_code_format_error(code)
        if reason:
            skipped.append({"code": code, "reason": reason})
            continue
        try:
            pen = add_pen(db, fid, PenAddIn(
                pen_code=code,
                pen_type=body.pen_type,
                species=species,
                capacity=body.capacity,
                remark=body.remark,
            ))
        except BizException as exc:
            # 校验失败都发生在写库前，回滚一次清掉可能残留的会话状态
            db.rollback()
            skipped.append({"code": code, "reason": exc.msg})
            continue
        except Exception:
            # 未知异常（如数据库约束冲突）：回滚本条后向上抛，交给全局处理器
            db.rollback()
            raise
        created_codes.append(pen.pen_code)

    return {
        "created": len(created_codes),
        "created_codes": created_codes,
        "skipped": skipped,
    }


def update_pen(db: Session, farm_id: int, pen_id: int, body: PenUpdateIn) -> Pen:
    pen = get_pen(db, farm_id, pen_id)
    original_code, original_species = pen.pen_code, pen.species

    # 先定下改后的畜种归属——编号查重要按改后的畜种算（换了畜种就等于换了编号命名空间）
    new_species = pen.species
    if body.species is not None:
        # 空串 = 清除归属，回到「待归属」状态
        new_species = (body.species or "").strip() or None
        validate_species(new_species, code=40017)
        # 改归属前，校验圈内现有畜禽是否都是该畜种，避免一个圈舍混养后被标成单一畜种
        if new_species and pen.current_count > 0:
            from app.modules.animal.model import Animal
            conflict = db.query(Animal).filter(
                Animal.pen_id == pen.id,
                Animal.farm_id == pen.farm_id,
                Animal.deleted == False,
                Animal.species != new_species,
            ).count()
            if conflict:
                raise BizException(
                    f"该圈舍内有 {conflict} 头非「{new_species}」畜禽，不能改为「{new_species}」",
                    code=40019,
                )
        pen.species = new_species

    if body.pen_code is not None:
        code = (body.pen_code or "").strip()
        if not code:
            raise BizException("圈舍编号不能为空", code=40012)
        if code != pen.pen_code:
            dup = db.query(Pen).filter(
                Pen.id != pen.id,
                Pen.farm_id == pen.farm_id,
                Pen.pen_code == code,
                Pen.deleted == False,
            ).filter(_pen_code_scope_filter(new_species)).first()
            if dup:
                raise BizException(
                    f"{_pen_code_scope_label(new_species)}圈舍编号 {code} 已存在",
                    code=40020,
                )
            pen.pen_code = code

    if body.pen_type is not None:
        pen.pen_type = body.pen_type
    if body.capacity is not None:
        if body.capacity < pen.current_count:
            raise BizException("新容量不能小于当前存栏数", code=40013)
        pen.capacity = body.capacity
    if body.status is not None:
        pen.status = body.status
    if body.remark is not None:
        pen.remark = body.remark

    # 编号或畜种变了才校验耳标号唯一，避免"只要碰这个圈舍就被历史冲突卡住"
    if pen.pen_code != original_code or pen.species != original_species:
        ensure_pen_tag_number_unique(db, pen.farm_id, pen.pen_code, pen.species, exclude_id=pen.id)

    db.commit()
    return pen


def delete_pen(db: Session, farm_id: int, pen_id: int):
    pen = get_pen(db, farm_id, pen_id)
    if pen.current_count > 0:
        raise BizException("圈舍内有畜禽，不能删除", code=40014)
    pen.deleted = True
    db.commit()


def find_available_pen(db: Session, farm_id: int, pen_type: str, species: str = None) -> Pen:
    """
    找一个有空位的圈舍（自动分配算法核心）
    按圈舍编号升序找第一个未满的圈舍
    - 传 species 时只挑本畜种的圈舍（未归属的圈舍也可用，随后由调用方自动归属）
    """
    fid = get_effective_farm_id(db, farm_id)
    query = db.query(Pen).filter(
        Pen.farm_id == fid,
        Pen.pen_type == pen_type,
        Pen.deleted == False,
        Pen.status == 1,
        Pen.current_count < Pen.capacity,
    )
    if species:
        query = query.filter(or_(Pen.species == species, Pen.species.is_(None)))
    pen = query.order_by(Pen.pen_code).first()

    if not pen:
        scope = f"{species}的" if species else ""
        raise BizException(f"{scope}类型 {pen_type} 的圈舍已满，请先添加圈舍", code=40015)
    return pen


def list_available_pens(db: Session, farm_id: int, pen_type: str, species: str = None) -> list[Pen]:
    """某类型下所有还有空位的圈舍（批量入栏分配用），同样按畜种隔离"""
    fid = get_effective_farm_id(db, farm_id)
    query = db.query(Pen).filter(
        Pen.farm_id == fid,
        Pen.pen_type == pen_type,
        Pen.deleted == False,
        Pen.status == 1,
        Pen.current_count < Pen.capacity,
    )
    if species:
        query = query.filter(or_(Pen.species == species, Pen.species.is_(None)))
    return query.order_by(Pen.pen_code).all()
