"""
销售财务业务逻辑

核心：出栏销售成本分摊算法（对应 DBD 8.2 sp_calc_animal_total_cost）
- feed_cost：耳标所在圈舍饲喂记录成本按当条记录的 animal_count 快照均分累加
  （入栏~出栏，仅审核通过）。单只只承担 1/当条头数，不再把整圈舍成本重复计入每头。
  口径说明：圈舍在栏历史无法从当前档案精确还原，此为按已记录头数的估算口径，
  转舍动物的早期圈舍记录无法追溯（记录头数缺失/为 0 的饲喂不参与个体分摊）
- medicine_cost：防疫/诊疗用药成本
  - 精确匹配：领用记录 related_module IN (防疫/诊疗) 且 related_id 命中该耳标
    审核通过的防疫/诊疗记录 → Σ 数量 × 单价快照
  - 兜底均摊：related_id 为空（未精确关联）的药品领用总额，按出栏当天存栏
    （在栏/待出栏/隔离/种用 + 本次出栏数）均摊
- labor_cost：月均人工成本 × 饲养天数 / 30 ÷ 在场只数（按只分摊；旧实现把整场月人工
  全额算进每一头，出栏成本被放大几十倍，是利润大额为负的主因之一）
- total_cost = feed + medicine + labor + consumable(恒 0，耗材成本口径未定义，不虚报)
- sale_amount = weight × unit_price；profit = sale_amount - total_cost
- 出栏后档案联动删除：动物档案转入历史记录表并逻辑删除（圈舍自动腾出），
  销售明细保留耳标/成本/利润快照，订单仍可完整追溯
- 利润汇总（profit_summary）改用「进货支出 + 物资消耗 + 人工薪资 + 其他成本」口径，
  不再把订单明细里的单只分摊成本当成整场饲养总成本
"""
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.models.user import User
from app.modules.animal.model import Animal
from app.modules.animal.service import (
    calc_age_days,
    determine_growth_stage,
    move_to_history,
)
from app.modules.pen.model import Pen
from app.modules.feeding.model import FeedingRecord
from app.modules.health.model import VaccineRecord, MedicalRecord
from app.modules.inventory.model import MaterialConsume, MaterialPurchase
from app.modules.salary.model import SalaryConfig
from app.modules.salary.service import DEFAULT_SALARY
from app.modules.finance.model import SaleOrder, SaleOrderDetail, CostExpense, SalaryRecord
from app.modules.finance.schema import (
    SaleOutIn, SaleOrderQuery, CostExpenseIn, CostExpenseUpdateIn, CostExpenseQuery,
    SalaryRecordQuery, EXPENSE_TYPES,
)

# 出栏允许的档案状态（种用/妊娠/死亡等不在内）
SALABLE_STATUSES = ("在栏", "待出栏")
SETTLE_UNSETTLED = "未结算"
SETTLE_SETTLED = "已结算"
# 利润汇总里归入「其他成本」的支出类型（自主录入的水电等实际支出）；
# 饲料/兽药/疫苗已由进货支出统计、人工已由薪资记录统计，这里不重复计入
OTHER_COST_TYPES = ("水电", "其他")


def _round2(v) -> float:
    return round(float(v or 0), 2)


# ============================================================
# 出栏销售
# ============================================================

def sale_out(db: Session, farm_id: int, body: SaleOutIn, user_id: int) -> SaleOrder:
    """出栏销售：生成订单+明细，档案转入历史记录（联动删除），圈舍自动腾出"""
    # 1. 校验耳标
    animals = []
    seen = set()
    for item in body.items:
        if item.ear_tag in seen:
            raise BizException(f"耳标 {item.ear_tag} 在本次销售中重复", code=40501)
        seen.add(item.ear_tag)
        animal = db.query(Animal).filter(
            Animal.farm_id == farm_id, Animal.ear_tag == item.ear_tag, Animal.deleted == False
        ).first()
        if not animal:
            raise BizException(f"耳标 {item.ear_tag} 的档案不存在", code=40502)
        if animal.status not in SALABLE_STATUSES:
            raise BizException(f"耳标 {item.ear_tag} 当前状态【{animal.status}】，不可出栏", code=40503)
        animals.append((animal, item.weight))

    order_date = body.order_date or date.today()
    sale_datetime = datetime.combine(order_date, datetime.min.time())
    species = animals[0][0].species

    # 2. 订单编号：SO + yyyyMMdd + 场内当日 3 位流水
    #    编号只在「本场」范围内唯一（各场独立编号），所以取本场当日已有编号的
    #    最大流水 +1，而不是简单用 count —— 历史数据里若有删号/跳号，
    #    count+1 会撞上已存在的编号。
    prefix = f"SO{order_date.strftime('%Y%m%d')}"
    existing_nos = {
        no for (no,) in db.query(SaleOrder.order_no).filter(
            SaleOrder.farm_id == farm_id, SaleOrder.order_no.like(f"{prefix}%")
        ).all()
    }
    seq = 1
    while f"{prefix}{seq:03d}" in existing_nos:
        seq += 1
    order_no = f"{prefix}{seq:03d}"

    order = SaleOrder(
        farm_id=farm_id, order_no=order_no,
        customer=body.customer, customer_phone=body.customer_phone,
        animal_count=0, total_weight=0, unit_price=body.unit_price, total_amount=0,
        order_date=sale_datetime, settle_status=SETTLE_UNSETTLED, species=species,
        remark=body.remark,
    )
    db.add(order)
    db.flush()

    total_weight = 0.0
    total_amount = 0.0
    # 未精确关联的药品领用总额 + 均摊基数（出栏当天在栏 + 本次出栏数），按只均摊
    unlinked_medicine_total, allot_base = _unlinked_medicine_allot(db, farm_id, len(animals))
    # 在场只数（人工成本分摊分母）：必须在循环外算一次，
    # 否则循环里逐头删除档案会让分母越来越小，后面出栏的畜禽人工成本越摊越多
    herd_size = _herd_size(db, farm_id)
    for animal, weight in animals:
        costs = _calc_animal_cost(
            db, farm_id, animal, order_date,
            unlinked_medicine_total, allot_base, herd_size,
        )
        sale_amount = _round2(weight * body.unit_price)
        total_cost = costs["total_cost"]
        profit = _round2(sale_amount - total_cost)
        profit_rate = _round2(profit / sale_amount * 100) if sale_amount else 0

        db.add(SaleOrderDetail(
            order_id=order.id, farm_id=farm_id,
            ear_tag=animal.ear_tag, archive_id=animal.id,
            species=animal.species, breed=animal.breed,
            weight=weight, raise_days=costs["raise_days"],
            feed_cost=costs["feed_cost"], medicine_cost=costs["medicine_cost"],
            labor_cost=costs["labor_cost"], consumable_cost=costs["consumable_cost"],
            total_cost=total_cost, sale_amount=sale_amount,
            profit=profit, profit_rate=profit_rate,
        ))
        total_weight += weight
        total_amount += sale_amount

        # 档案联动删除：先标记"已出栏 + 出栏日期"（让历史快照里能看到已出栏），
        # 再转入历史记录表并逻辑删除 —— 档案管理列表不再出现这头畜禽。
        # 圈舍存栏 -1（圈舍自动腾出）由 move_to_history 统一处理，这里不要重复扣。
        animal.status = "已出栏"
        animal.out_date = order_date
        # 状态已被改成「已出栏」，move_to_history 默认按当前状态判断是否腾位，
        # 这里显式传 True：出栏的这头原本是占圈的，必须腾出。
        move_to_history(db, animal, order_date, release_capacity=True)

    order.animal_count = len(animals)
    order.total_weight = _round2(total_weight)
    order.total_amount = _round2(total_amount)
    db.commit()
    return order


def _calc_animal_cost(db: Session, farm_id: int, animal: Animal, out_date: date,
                      unlinked_medicine_total: float = 0.0, allot_base: int = 0,
                      herd_size: int = 0) -> dict:
    """计算单只饲养成本（DBD 8.2 sp_calc_animal_total_cost）"""
    in_date = animal.in_date or out_date
    raise_days = max((out_date - in_date).days, 0)

    # 饲料成本：所在圈舍饲喂记录成本按当条记录的 animal_count 快照均分（审核通过）。
    # 每条记录单只只承担 feed_cost / animal_count，多只动物分摊之和等于记录总额，
    # 不再把整圈舍成本重复计入每一头。头数缺失/为 0 的记录无法定义分摊口径，跳过不计（不除零）。
    feed_cost = 0
    if animal.pen_id:
        per_record_share = case(
            (
                FeedingRecord.animal_count > 0,
                func.coalesce(FeedingRecord.feed_cost, 0) / FeedingRecord.animal_count,
            ),
            else_=0,
        )
        feed_cost = db.query(func.coalesce(func.sum(per_record_share), 0)).filter(
            FeedingRecord.farm_id == farm_id,
            FeedingRecord.pen_id == animal.pen_id,
            FeedingRecord.feed_date >= in_date,
            FeedingRecord.feed_date <= out_date,
            FeedingRecord.audit_status == "通过",
            FeedingRecord.deleted == False,
        ).scalar() or 0

    # 药品疫苗成本：
    # 1) 精确匹配——领用记录关联到该耳标审核通过的防疫/诊疗记录 → Σ 数量 × 单价快照
    medicine_cost = 0.0
    related_ids = set()
    vaccine_ids = [r.id for r in db.query(VaccineRecord.id).filter(
        VaccineRecord.farm_id == farm_id,
        VaccineRecord.ear_tag == animal.ear_tag,
        VaccineRecord.audit_status == "通过",
        VaccineRecord.deleted == False,
    ).all()]
    medical_ids = [r.id for r in db.query(MedicalRecord.id).filter(
        MedicalRecord.farm_id == farm_id,
        MedicalRecord.ear_tag == animal.ear_tag,
        MedicalRecord.audit_status == "通过",
        MedicalRecord.deleted == False,
    ).all()]
    related_ids.update(vaccine_ids)
    related_ids.update(medical_ids)
    if related_ids:
        consume_rows = db.query(MaterialConsume).filter(
            MaterialConsume.farm_id == farm_id,
            MaterialConsume.related_module.in_(("防疫", "诊疗")),
            MaterialConsume.related_id.in_(related_ids),
            MaterialConsume.audit_status == "通过",
            MaterialConsume.deleted == False,
        ).all()
        medicine_cost = sum(
            float(c.quantity or 0) * float(c.unit_price or 0) for c in consume_rows
        )
    # 2) 兜底均摊——related_id 为空（未精确关联）的药品领用，按出栏当天存栏只数均摊
    if allot_base > 0 and unlinked_medicine_total > 0:
        medicine_cost += unlinked_medicine_total / allot_base

    # 分摊人工成本：月均人工 × 饲养天数 / 30，再按同期在场只数摊到单只
    # 旧实现把整场月人工**全额**算到每一只头上：29 头牛就等于交了 29 份人工，
    # 出栏成本被放大几十倍，利润必然是负的。这里除以在场只数，保证
    # 「所有在场畜禽的人工分摊之和 ≈ 整场人工成本」。
    labor_cost = 0.0
    if herd_size > 0:
        labor_cost = _avg_monthly_labor(db, farm_id) * raise_days / 30 / herd_size

    # 各分项先四舍五入再求和，保证 明细四项之和 == total_cost（不出现分项舍入后对不上的情况）
    feed_cost = _round2(feed_cost)
    medicine_cost = _round2(medicine_cost)
    labor_cost = _round2(labor_cost)
    consumable_cost = _round2(0)
    return {
        "raise_days": raise_days,
        "feed_cost": feed_cost,
        "medicine_cost": medicine_cost,
        "labor_cost": labor_cost,
        "consumable_cost": consumable_cost,
        "total_cost": _round2(feed_cost + medicine_cost + labor_cost + consumable_cost),
    }


def _unlinked_medicine_allot(db: Session, farm_id: int, sale_count: int) -> tuple:
    """
    计算未精确关联的药品/疫苗领用成本均摊参数：
    - 总额：物资类型为疫苗/兽药、related_id 为空（未精确关联到防疫/诊疗记录）、
      审核通过的领用金额合计（精确匹配部分已按记录归属到对应耳标，不会重复）
    - 基数：出栏当天仍在栏（在栏/待出栏/隔离/种用）的头数 + 本次出栏头数
    返回 (总额, 基数)；基数为 0 时返回 (0, 0) 不摊。
    """
    total = db.query(func.coalesce(
        func.sum(MaterialConsume.quantity * func.coalesce(MaterialConsume.unit_price, 0)), 0
    )).filter(
        MaterialConsume.farm_id == farm_id,
        MaterialConsume.material_type.in_(("疫苗", "兽药")),
        MaterialConsume.related_id.is_(None),
        MaterialConsume.audit_status == "通过",
        MaterialConsume.deleted == False,
    ).scalar() or 0

    base = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.status.in_(("在栏", "待出栏", "隔离", "种用")),
        Animal.deleted == False,
    ).count() + sale_count
    total = float(total)
    return (round(total, 2), base) if base > 0 else (0.0, 0)


def _herd_size(db: Session, farm_id: int) -> int:
    """在场只数（在栏/待出栏/隔离/种用），作为人工成本的分摊分母"""
    return db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.status.in_(("在栏", "待出栏", "隔离", "种用")),
        Animal.deleted == False,
    ).count()


def _avg_monthly_labor(db: Session, farm_id: int) -> float:
    """月均人工成本：优先薪资记录实发均值，否则薪资配置基础薪资均值"""
    rec = db.query(func.avg(SalaryRecord.actual_pay)).filter(
        SalaryRecord.farm_id == farm_id, SalaryRecord.deleted == False
    ).scalar()
    if rec:
        return float(rec)
    avg = db.query(func.avg(SalaryConfig.base_salary)).filter(
        SalaryConfig.farm_id == farm_id, SalaryConfig.deleted == False
    ).scalar()
    if avg:
        return float(avg)
    return float(sum(DEFAULT_SALARY.values()) / len(DEFAULT_SALARY))


def list_orders(db: Session, farm_id: int, query: SaleOrderQuery) -> dict:
    """销售订单列表（分页 + 多条件）"""
    q = db.query(SaleOrder).filter(SaleOrder.farm_id == farm_id, SaleOrder.deleted == False)
    if query.order_no:
        q = q.filter(SaleOrder.order_no.like(f"%{query.order_no}%"))
    if query.customer:
        q = q.filter(SaleOrder.customer.like(f"%{query.customer}%"))
    if query.species:
        q = q.filter(SaleOrder.species == query.species)
    if query.settle_status:
        q = q.filter(SaleOrder.settle_status == query.settle_status)
    if query.start_date:
        q = q.filter(SaleOrder.order_date >= query.start_date)
    if query.end_date:
        q = q.filter(SaleOrder.order_date <= query.end_date + timedelta(days=1))

    total = q.count()
    items = q.order_by(SaleOrder.order_date.desc(), SaleOrder.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_order(db: Session, farm_id: int, order_id: int):
    """订单详情（含明细）"""
    order = db.query(SaleOrder).filter(
        SaleOrder.id == order_id, SaleOrder.farm_id == farm_id, SaleOrder.deleted == False
    ).first()
    if not order:
        raise BizException("销售订单不存在", code=40510)
    details = db.query(SaleOrderDetail).filter(
        SaleOrderDetail.order_id == order.id, SaleOrderDetail.deleted == False
    ).order_by(SaleOrderDetail.id).all()
    return order, details


def settle_order(db: Session, farm_id: int, order_id: int) -> SaleOrder:
    order, _ = get_order(db, farm_id, order_id)
    if order.settle_status == SETTLE_SETTLED:
        raise BizException("该订单已结算", code=40511)
    order.settle_status = SETTLE_SETTLED
    order.settle_time = datetime.now()
    db.commit()
    return order


def list_sale_candidates(db: Session, farm_id: int, species: Optional[str] = None,
                         growth_stage: Optional[str] = None, keyword: Optional[str] = None) -> List[dict]:
    """
    出栏候选畜禽：在栏/待出栏的档案。

    生长阶段按出生日期**实时计算**，不直接读 animal_archive.growth_stage ——
    那一列只在入栏时写一次 + 每日 00:05 定时刷新，会和档案管理页（接口层实时算）
    显示不一致，用户看到的就是「档案里是育肥期、销售订单里是生长期」。
    妊娠个体保留「妊娠」标记（由配种记录写入，不能按日龄覆盖）。
    """
    q = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.status.in_(SALABLE_STATUSES), Animal.deleted == False
    )
    if species:
        q = q.filter(Animal.species == species)
    if keyword:
        q = q.filter(Animal.ear_tag.like(f"%{keyword}%"))
    animals = q.order_by(Animal.species, Animal.ear_tag).all()

    out = []
    for a in animals:
        age_days = calc_age_days(a.birth_date)
        stage = a.growth_stage if a.growth_stage == "妊娠" else determine_growth_stage(a.species, age_days)
        # 生长阶段筛选也按实时值过滤（存储值可能已经陈旧）
        if growth_stage and stage != growth_stage:
            continue
        out.append({
            "id": a.id, "ear_tag": a.ear_tag, "species": a.species, "breed": a.breed,
            "gender": a.gender, "pen_id": a.pen_id, "in_date": a.in_date,
            "growth_stage": stage, "age_days": age_days, "status": a.status,
        })
    return out


# ============================================================
# 成本支出
# ============================================================

def add_expense(db: Session, farm_id: int, body: CostExpenseIn) -> CostExpense:
    _validate_expense_type(body.expense_type)
    exp = CostExpense(farm_id=farm_id, **body.model_dump())
    db.add(exp)
    db.commit()
    return exp


def list_expenses(db: Session, farm_id: int, query: CostExpenseQuery) -> dict:
    q = db.query(CostExpense).filter(CostExpense.farm_id == farm_id, CostExpense.deleted == False)
    if query.expense_type:
        q = q.filter(CostExpense.expense_type == query.expense_type)
    if query.start_date:
        q = q.filter(CostExpense.expense_date >= query.start_date)
    if query.end_date:
        q = q.filter(CostExpense.expense_date <= query.end_date)

    total = q.count()
    items = q.order_by(CostExpense.expense_date.desc(), CostExpense.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_expense(db: Session, farm_id: int, expense_id: int) -> CostExpense:
    exp = db.query(CostExpense).filter(
        CostExpense.id == expense_id, CostExpense.farm_id == farm_id, CostExpense.deleted == False
    ).first()
    if not exp:
        raise BizException("成本支出记录不存在", code=40521)
    return exp


def update_expense(db: Session, farm_id: int, expense_id: int, body: CostExpenseUpdateIn) -> CostExpense:
    exp = get_expense(db, farm_id, expense_id)
    data = body.model_dump(exclude_unset=True)
    if "expense_type" in data and data["expense_type"]:
        _validate_expense_type(data["expense_type"])
    for k, v in data.items():
        setattr(exp, k, v)
    db.commit()
    return exp


def delete_expense(db: Session, farm_id: int, expense_id: int):
    exp = get_expense(db, farm_id, expense_id)
    exp.deleted = True
    db.commit()


def _validate_expense_type(expense_type: str):
    if expense_type not in EXPENSE_TYPES:
        raise BizException(f"支出类型只能是：{'/'.join(EXPENSE_TYPES)}", code=40520)


# ============================================================
# 利润汇总
# ============================================================

def profit_summary(db: Session, farm_id: int, start_date: Optional[date] = None,
                   end_date: Optional[date] = None) -> dict:
    """
    时间段利润汇总

    口径（按优化需求单整理，各项独立统计、互不混算）：
    - 订单数 / 销售数量 / 销售金额：来自销售订单明细（按订单日期过滤）
    - 进货支出总成本：审核通过的进货记录金额（数量 × 进货单价），含饲料/兽药/疫苗等
    - 物资消耗总成本：审核通过的领用记录金额（数量 × 领用单价快照），即实际用掉的物资
    - 人工薪资总成本：薪资记录实发合计（发放月份落在查询区间内；未生成薪资记录时为 0）
    - 其他成本：成本支出里「水电/其他」两类由用户自主录入的支出
    - 饲养总成本 = 进货支出 + 物资消耗 + 人工薪资 + 其他
    - 盈利金额 = 销售金额 - 饲养总成本
    - 利润率 = 盈利金额 / 销售金额 × 100

    之前的问题：饲养总成本直接取订单明细里的 total_cost（单只分摊成本）之和，
    与销售金额口径不匹配，页面还把它和「销售利润」「成本支出」混着算，
    出现销售额 143500、饲养总成本 300375、利润率 -109% 这种明显不合理的数字。
    """
    # ---------- 销售端 ----------
    dq = db.query(SaleOrderDetail).join(SaleOrder, SaleOrder.id == SaleOrderDetail.order_id).filter(
        SaleOrderDetail.farm_id == farm_id,
        SaleOrderDetail.deleted == False,
        SaleOrder.farm_id == farm_id,
        SaleOrder.deleted == False,
    )
    if start_date:
        dq = dq.filter(SaleOrder.order_date >= start_date)
    if end_date:
        dq = dq.filter(SaleOrder.order_date <= end_date + timedelta(days=1))
    rows = dq.all()

    order_ids = set()
    animal_count = 0
    total_amount = 0.0
    for detail in rows:
        order_ids.add(detail.order_id)
        animal_count += 1
        total_amount += float(detail.sale_amount or 0)

    # ---------- 进货支出（关联物资库存的进货记录） ----------
    pq = db.query(func.coalesce(func.sum(
        func.coalesce(MaterialPurchase.total_cost,
                      MaterialPurchase.quantity * MaterialPurchase.cost_price)
    ), 0)).filter(
        MaterialPurchase.farm_id == farm_id,
        MaterialPurchase.audit_status == "通过",
        MaterialPurchase.deleted == False,
    )
    if start_date:
        pq = pq.filter(MaterialPurchase.purchase_date >= start_date)
    if end_date:
        pq = pq.filter(MaterialPurchase.purchase_date <= end_date)
    purchase_cost = float(pq.scalar() or 0)

    # ---------- 物资消耗（关联领用记录：饲料/药物/疫苗实际使用量） ----------
    cq = db.query(func.coalesce(func.sum(
        MaterialConsume.quantity * func.coalesce(MaterialConsume.unit_price, 0)
    ), 0)).filter(
        MaterialConsume.farm_id == farm_id,
        MaterialConsume.audit_status == "通过",
        MaterialConsume.deleted == False,
    )
    if start_date:
        cq = cq.filter(MaterialConsume.consume_date >= start_date)
    if end_date:
        cq = cq.filter(MaterialConsume.consume_date <= end_date)
    consume_cost = float(cq.scalar() or 0)

    # ---------- 人工薪资（只统计已发放的薪资记录；待发放尚未实际支出，不计入成本） ----------
    sq = db.query(func.coalesce(func.sum(SalaryRecord.actual_pay), 0)).filter(
        SalaryRecord.farm_id == farm_id,
        SalaryRecord.deleted == False,
        SalaryRecord.status == "已发放",
    )
    if start_date:
        sq = sq.filter(SalaryRecord.pay_month >= start_date.strftime("%Y-%m"))
    if end_date:
        sq = sq.filter(SalaryRecord.pay_month <= end_date.strftime("%Y-%m"))
    labor_cost = float(sq.scalar() or 0)

    # 待发放金额单独返回，前端可作为"待发生成本"提示，不进入饲养总成本
    pq = db.query(func.coalesce(func.sum(SalaryRecord.actual_pay), 0)).filter(
        SalaryRecord.farm_id == farm_id,
        SalaryRecord.deleted == False,
        SalaryRecord.status != "已发放",
    )
    if start_date:
        pq = pq.filter(SalaryRecord.pay_month >= start_date.strftime("%Y-%m"))
    if end_date:
        pq = pq.filter(SalaryRecord.pay_month <= end_date.strftime("%Y-%m"))
    labor_pending = float(pq.scalar() or 0)

    # ---------- 其他成本（自主录入的水电/其他支出） ----------
    def _expense_sum(types_only: bool):
        q = db.query(func.coalesce(func.sum(CostExpense.amount), 0)).filter(
            CostExpense.farm_id == farm_id, CostExpense.deleted == False
        )
        if types_only:
            q = q.filter(CostExpense.expense_type.in_(OTHER_COST_TYPES))
        if start_date:
            q = q.filter(CostExpense.expense_date >= start_date)
        if end_date:
            q = q.filter(CostExpense.expense_date <= end_date)
        return float(q.scalar() or 0)

    other_cost = _expense_sum(True)
    expense_amount = _expense_sum(False)

    # ---------- 汇总 ----------
    total_amount = _round2(total_amount)
    purchase_cost = _round2(purchase_cost)
    consume_cost = _round2(consume_cost)
    labor_cost = _round2(labor_cost)
    other_cost = _round2(other_cost)
    breeding_cost = _round2(purchase_cost + consume_cost + labor_cost + other_cost)
    profit = _round2(total_amount - breeding_cost)
    profit_rate = _round2(profit / total_amount * 100) if total_amount else 0
    return {
        "order_count": len(order_ids),
        "animal_count": animal_count,
        "total_amount": total_amount,
        "purchase_cost": purchase_cost,
        "consume_cost": consume_cost,
        "labor_cost": labor_cost,
        "labor_pending": _round2(labor_pending),
        "other_cost": other_cost,
        "breeding_cost": breeding_cost,
        # 兼容旧字段（统计分析页仍在读）
        "total_cost": breeding_cost,
        "profit": profit,
        "total_profit": profit,
        "profit_rate": profit_rate,
        "expense_amount": _round2(expense_amount),
        "net_profit": profit,
    }


# ============================================================
# 薪资记录
# ============================================================

def generate_salary(db: Session, farm_id: int, pay_month: str) -> int:
    """按月生成在职员工薪资记录（防重：同人同月只生成一次）"""
    employees = db.query(User).filter(
        User.farm_id == farm_id, User.user_type == 3, User.status == 1, User.deleted == False
    ).all()
    configs = {
        c.post: float(c.base_salary)
        for c in db.query(SalaryConfig).filter(SalaryConfig.farm_id == farm_id, SalaryConfig.deleted == False).all()
    }
    created = 0
    for emp in employees:
        post = emp.post or "饲喂员"
        exists = db.query(SalaryRecord).filter(
            SalaryRecord.farm_id == farm_id,
            SalaryRecord.user_id == emp.id,
            SalaryRecord.pay_month == pay_month,
            SalaryRecord.deleted == False,
        ).first()
        if exists:
            continue
        base = configs.get(post) or DEFAULT_SALARY.get(post, 0)
        db.add(SalaryRecord(
            farm_id=farm_id, user_id=emp.id, post=post, pay_month=pay_month,
            base_salary=base, bonus=0, deduct=0, actual_pay=base, status="待发放",
        ))
        created += 1
    db.commit()
    return created


def list_salaries(db: Session, farm_id: int, query: SalaryRecordQuery) -> dict:
    q = db.query(SalaryRecord, User).join(User, User.id == SalaryRecord.user_id).filter(
        SalaryRecord.farm_id == farm_id, SalaryRecord.deleted == False
    )
    if query.pay_month:
        q = q.filter(SalaryRecord.pay_month == query.pay_month)
    if query.post:
        q = q.filter(SalaryRecord.post == query.post)
    if query.status:
        q = q.filter(SalaryRecord.status == query.status)

    total = q.count()
    rows = q.order_by(SalaryRecord.pay_month.desc(), SalaryRecord.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    items = [_salary_out(rec, user) for rec, user in rows]
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def pay_salary(db: Session, farm_id: int, record_id: int) -> SalaryRecord:
    rec = db.query(SalaryRecord).filter(
        SalaryRecord.id == record_id, SalaryRecord.farm_id == farm_id, SalaryRecord.deleted == False
    ).first()
    if not rec:
        raise BizException("薪资记录不存在", code=40530)
    if rec.status == "已发放":
        raise BizException("该薪资记录已发放", code=40531)
    rec.status = "已发放"
    rec.pay_time = datetime.now()
    db.commit()
    return rec


def _salary_out(rec: SalaryRecord, user: User) -> dict:
    return {
        "id": rec.id, "user_id": rec.user_id,
        "username": user.username if user else None,
        "real_name": user.real_name if user else None,
        "post": rec.post, "pay_month": rec.pay_month,
        "base_salary": float(rec.base_salary), "bonus": float(rec.bonus),
        "deduct": float(rec.deduct), "actual_pay": float(rec.actual_pay),
        "pay_time": rec.pay_time, "status": rec.status, "remark": rec.remark,
    }
