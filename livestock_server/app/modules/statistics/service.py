"""
统计业务逻辑（P3-1）

5 个只读统计接口，全部为聚合查询，无新增表：
- dashboard：综合数据大屏（KPI + 近12月入栏/出栏趋势 + 畜种/阶段分布）
- breeding：存栏繁育统计（存栏分布 + 配种/产犊 + 待处理预警 + 产犊趋势）
- health：防疫诊疗统计（疫苗/病情/诊疗状态分布 + 月度趋势）
- material：物资消耗统计（库存状态 + 本月进货/领用 + 领用趋势）
- finance：财务统计（利润汇总复用 finance.profit_summary + 月度销售利润趋势 + 支出分布）

统计口径：
- 存栏 = status ∈ 在栏/种用/隔离/待出栏 的未删除档案
- 趋势 = 按自然月统计近 12 个月
- 分布用 ORM 拉取后在 Python 分组（单养殖场数据量小，跨 MySQL/SQLite 通用、便于测试）
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.animal.model import Animal
from app.modules.breeding.model import MatingRecord, BirthRecord, BreedingAlert
from app.modules.feeding.model import FeedingRecord
from app.modules.finance.model import SaleOrder, SaleOrderDetail, CostExpense
from app.modules.finance.service import profit_summary
from app.modules.health.model import VaccineRecord, MedicalRecord
from app.modules.inventory.model import MaterialStock, MaterialPurchase, MaterialConsume
from app.modules.inventory.service import _refresh_stock_status

# 存栏状态（不计入已出栏/死亡）
ACTIVE_STATUSES = ("在栏", "种用", "隔离", "待出栏")
# 审核类记录（待审核聚合）
AUDIT_MODELS = (FeedingRecord, MaterialPurchase, MaterialConsume, VaccineRecord, MedicalRecord)


def _last_n_month_keys(n: int = 12) -> list[str]:
    """近 n 个月的月份 key（YYYY-MM），从旧到新"""
    keys = []
    y, m = date.today().year, date.today().month
    for _ in range(n):
        keys.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    keys.reverse()
    return keys


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _dist(rows, key_fn) -> list[dict]:
    """按 key 分组计数，返回 [{name, value}]，按数量降序"""
    counts: dict[str, int] = {}
    for r in rows:
        k = key_fn(r)
        if not k:
            continue
        counts[k] = counts.get(k, 0) + 1
    items = sorted(counts.items(), key=lambda kv: -kv[1])
    return [{"name": k, "value": v} for k, v in items]


def _sum_dist(rows, key_fn, val_fn) -> list[dict]:
    """按 key 分组求和，返回 [{name, value}]，按金额降序"""
    sums: dict[str, float] = {}
    for r in rows:
        k = key_fn(r)
        if not k:
            continue
        sums[k] = sums.get(k, 0) + float(val_fn(r) or 0)
    items = sorted(sums.items(), key=lambda kv: -kv[1])
    return [{"name": k, "value": round(v, 2)} for k, v in items]


def _trend_map(rows, key_fn, months: list[str]) -> dict[str, int]:
    counts = {m: 0 for m in months}
    for r in rows:
        k = key_fn(r)
        if k in counts:
            counts[k] += 1
    return counts


def _stock_q(db: Session, farm_id: int):
    return db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.deleted == False,
        Animal.status.in_(ACTIVE_STATUSES),
    )


def _month_start(today: date) -> date:
    return today.replace(day=1)


# ============================================================
# 1. 综合数据大屏
# ============================================================

def dashboard_stats(db: Session, farm_id: int) -> dict:
    today = date.today()
    m_start = _month_start(today)
    since = (_month_start(today - timedelta(days=31 * 11)))

    # ---- KPI ----
    today_stock = _stock_q(db, farm_id).count()
    month_in = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.deleted == False,
        Animal.in_date >= m_start,
    ).count()
    month_out = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.deleted == False,
        Animal.out_date >= m_start,
    ).count()

    detail_rows = db.query(SaleOrderDetail).join(
        SaleOrder, SaleOrder.id == SaleOrderDetail.order_id
    ).filter(
        SaleOrderDetail.farm_id == farm_id,
        SaleOrderDetail.deleted == False,
        SaleOrder.deleted == False,
    ).all()
    total_sale = round(sum(float(d.sale_amount or 0) for d in detail_rows), 2)
    total_profit = round(sum(float(d.profit or 0) for d in detail_rows), 2)

    pending_audit = sum(
        db.query(mod).filter(
            mod.farm_id == farm_id, mod.deleted == False, mod.audit_status == "待审核"
        ).count() for mod in AUDIT_MODELS
    )
    pending_alert = db.query(BreedingAlert).filter(
        BreedingAlert.farm_id == farm_id, BreedingAlert.deleted == False,
        BreedingAlert.status == "待处理",
    ).count()
    staff_count = db.query(User).filter(
        User.farm_id == farm_id, User.deleted == False
    ).count()

    # ---- 近 12 月入栏/出栏趋势 ----
    months = _last_n_month_keys()
    in_rows = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.deleted == False,
        Animal.in_date.isnot(None), Animal.in_date >= since,
    ).all()
    out_rows = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.deleted == False,
        Animal.out_date.isnot(None), Animal.out_date >= since,
    ).all()
    in_map = _trend_map(in_rows, lambda a: _month_key(a.in_date), months)
    out_map = _trend_map(out_rows, lambda a: _month_key(a.out_date), months)

    # ---- 当前存栏分布 ----
    animals = _stock_q(db, farm_id).all()
    species_dist = _dist(animals, lambda a: a.species)
    stage_dist = _dist(animals, lambda a: a.growth_stage)

    return {
        "kpi": {
            "today_stock": today_stock,
            "month_in": month_in,
            "month_out": month_out,
            "total_sale": total_sale,
            "total_profit": total_profit,
            "pending_audit": pending_audit,
            "pending_alert": pending_alert,
            "staff_count": staff_count,
        },
        "stock_trend": {
            "months": months,
            "in_values": [in_map[m] for m in months],
            "out_values": [out_map[m] for m in months],
        },
        "species_dist": species_dist,
        "stage_dist": stage_dist,
    }


# ============================================================
# 2. 存栏繁育统计
# ============================================================

def breeding_stats(db: Session, farm_id: int) -> dict:
    today = date.today()
    m_start = _month_start(today)
    since = _month_start(today - timedelta(days=31 * 11))

    animals = _stock_q(db, farm_id).all()
    current_stock = len(animals)
    species_dist = _dist(animals, lambda a: a.species)
    gender_dist = _dist(animals, lambda a: a.gender)
    stage_dist = _dist(animals, lambda a: a.growth_stage)
    pen_dist = _dist(animals, lambda a: f"圈舍{a.pen_id}" if a.pen_id else "未分配")

    month_mating = db.query(MatingRecord).filter(
        MatingRecord.farm_id == farm_id, MatingRecord.deleted == False,
        MatingRecord.mating_date >= m_start,
    ).count()
    month_birth = db.query(BirthRecord).filter(
        BirthRecord.farm_id == farm_id, BirthRecord.deleted == False,
        BirthRecord.birth_date >= m_start,
    ).count()
    pregnant_count = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.deleted == False,
        Animal.growth_stage == "妊娠",
    ).count()

    alerts = db.query(BreedingAlert).filter(
        BreedingAlert.farm_id == farm_id, BreedingAlert.deleted == False,
        BreedingAlert.status == "待处理",
    ).all()
    alert_dist = _dist(alerts, lambda a: a.alert_type)

    months = _last_n_month_keys()
    birth_rows = db.query(BirthRecord).filter(
        BirthRecord.farm_id == farm_id, BirthRecord.deleted == False,
        BirthRecord.birth_date >= since,
    ).all()
    birth_map = _trend_map(birth_rows, lambda b: _month_key(b.birth_date), months)

    return {
        "current_stock": current_stock,
        "species_dist": species_dist,
        "gender_dist": gender_dist,
        "stage_dist": stage_dist,
        "pen_dist": pen_dist,
        "month_mating": month_mating,
        "month_birth": month_birth,
        "pregnant_count": pregnant_count,
        "alert_dist": alert_dist,
        "birth_trend": {"months": months, "values": [birth_map[m] for m in months]},
    }


# ============================================================
# 3. 防疫诊疗统计
# ============================================================

def health_stats(db: Session, farm_id: int) -> dict:
    today = date.today()
    m_start = _month_start(today)
    since = _month_start(today - timedelta(days=31 * 11))

    month_vaccine = db.query(VaccineRecord).filter(
        VaccineRecord.farm_id == farm_id, VaccineRecord.deleted == False,
        VaccineRecord.vaccine_date >= m_start,
    ).count()
    month_medical = db.query(MedicalRecord).filter(
        MedicalRecord.farm_id == farm_id, MedicalRecord.deleted == False,
        MedicalRecord.medical_date >= m_start,
    ).count()

    # 分布只看已通过审核的记录（驳回的未实际执行）
    approved_vaccines = db.query(VaccineRecord).filter(
        VaccineRecord.farm_id == farm_id, VaccineRecord.deleted == False,
        VaccineRecord.audit_status == "通过",
    ).all()
    approved_medicals = db.query(MedicalRecord).filter(
        MedicalRecord.farm_id == farm_id, MedicalRecord.deleted == False,
        MedicalRecord.audit_status == "通过",
    ).all()
    vaccine_dist = _dist(approved_vaccines, lambda v: v.vaccine_type)
    disease_dist = _dist(approved_medicals, lambda m: m.disease_type)
    treatment_dist = _dist(approved_medicals, lambda m: m.treatment_status)

    months = _last_n_month_keys()
    vaccine_rows = db.query(VaccineRecord).filter(
        VaccineRecord.farm_id == farm_id, VaccineRecord.deleted == False,
        VaccineRecord.vaccine_date >= since,
    ).all()
    medical_rows = db.query(MedicalRecord).filter(
        MedicalRecord.farm_id == farm_id, MedicalRecord.deleted == False,
        MedicalRecord.medical_date >= since,
    ).all()
    vaccine_map = _trend_map(vaccine_rows, lambda v: _month_key(v.vaccine_date), months)
    medical_map = _trend_map(medical_rows, lambda m: _month_key(m.medical_date), months)

    return {
        "month_vaccine": month_vaccine,
        "month_medical": month_medical,
        "vaccine_dist": vaccine_dist,
        "disease_dist": disease_dist,
        "treatment_dist": treatment_dist,
        "health_trend": {
            "months": months,
            "vaccine_values": [vaccine_map[m] for m in months],
            "medical_values": [medical_map[m] for m in months],
        },
    }


# ============================================================
# 4. 物资消耗统计
# ============================================================

def material_stats(db: Session, farm_id: int) -> dict:
    today = date.today()
    m_start = _month_start(today)
    since = _month_start(today - timedelta(days=31 * 11))

    stocks = db.query(MaterialStock).filter(
        MaterialStock.farm_id == farm_id, MaterialStock.deleted == False,
    ).all()
    # 状态是动态算的，先刷新再分组（不落库）
    for s in stocks:
        _refresh_stock_status(s)

    type_dist = _dist(stocks, lambda s: s.material_type)
    status_dist = _dist(stocks, lambda s: s.status)
    shortage_count = sum(1 for s in stocks if s.is_shortage == 1)
    expired_count = sum(1 for s in stocks if s.status == "已过期")
    expiring_count = sum(1 for s in stocks if s.status == "即将过期")

    month_purchase_amount = round(sum(
        float(p.total_cost or 0) for p in db.query(MaterialPurchase).filter(
            MaterialPurchase.farm_id == farm_id, MaterialPurchase.deleted == False,
            MaterialPurchase.purchase_date >= m_start,
        ).all()
    ), 2)

    months = _last_n_month_keys()
    consume_rows = db.query(MaterialConsume).filter(
        MaterialConsume.farm_id == farm_id, MaterialConsume.deleted == False,
        MaterialConsume.consume_date >= since,
    ).all()
    month_consume = sum(
        float(c.quantity or 0) for c in consume_rows if c.consume_date >= m_start
    )
    consume_vals = {m: 0.0 for m in months}
    for c in consume_rows:
        k = _month_key(c.consume_date)
        if k in consume_vals:
            consume_vals[k] += float(c.quantity or 0)

    return {
        "stock_count": len(stocks),
        "type_dist": type_dist,
        "status_dist": status_dist,
        "shortage_count": shortage_count,
        "expired_count": expired_count,
        "expiring_count": expiring_count,
        "month_purchase_amount": month_purchase_amount,
        "month_consume": round(month_consume, 2),
        "consume_trend": {
            "months": months,
            "values": [round(consume_vals[m], 2) for m in months],
        },
    }


# ============================================================
# 5. 财务统计
# ============================================================

def finance_stats(db: Session, farm_id: int) -> dict:
    today = date.today()
    m_start = _month_start(today)
    since = _month_start(today - timedelta(days=31 * 11))

    total = profit_summary(db, farm_id)
    month = profit_summary(db, farm_id, m_start, today)

    # 近 12 月销售额/利润趋势（按订单月份聚合明细）
    months = _last_n_month_keys()
    detail_rows = db.query(SaleOrderDetail, SaleOrder).join(
        SaleOrder, SaleOrder.id == SaleOrderDetail.order_id
    ).filter(
        SaleOrderDetail.farm_id == farm_id,
        SaleOrderDetail.deleted == False,
        SaleOrder.deleted == False,
        SaleOrder.order_date >= since,
    ).all()
    sale_vals = {m: 0.0 for m in months}
    profit_vals = {m: 0.0 for m in months}
    for detail, order in detail_rows:
        k = _month_key(order.order_date.date())
        if k in sale_vals:
            sale_vals[k] += float(detail.sale_amount or 0)
            profit_vals[k] += float(detail.profit or 0)

    expenses = db.query(CostExpense).filter(
        CostExpense.farm_id == farm_id, CostExpense.deleted == False,
    ).all()
    expense_dist = _sum_dist(expenses, lambda e: e.expense_type, lambda e: e.amount)

    return {
        "total": total,
        "month": month,
        "profit_trend": {
            "months": months,
            "sale_values": [round(sale_vals[m], 2) for m in months],
            "profit_values": [round(profit_vals[m], 2) for m in months],
        },
        "expense_dist": expense_dist,
    }
