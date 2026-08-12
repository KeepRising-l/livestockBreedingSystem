"""
销售财务业务逻辑

核心：出栏销售成本分摊算法（对应 DBD 8.2 sp_calc_animal_total_cost）
- feed_cost：耳标所在圈舍饲喂记录成本累加（入栏~出栏，仅审核通过）
- medicine_cost：防疫/诊疗用药成本（当前物资表无单价，置 0）
- labor_cost：月均人工成本 × 饲养天数 / 30
- total_cost = feed + medicine + labor + consumable(0)
- sale_amount = weight × unit_price；profit = sale_amount - total_cost
"""
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.models.user import User
from app.modules.animal.model import Animal
from app.modules.pen.model import Pen
from app.modules.feeding.model import FeedingRecord
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


def _round2(v) -> float:
    return round(float(v or 0), 2)


# ============================================================
# 出栏销售
# ============================================================

def sale_out(db: Session, farm_id: int, body: SaleOutIn, user_id: int) -> SaleOrder:
    """出栏销售：生成订单+明细，档案置已出栏，圈舍存栏减 1"""
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

    # 2. 订单编号：SO + yyyyMMdd + 当日 3 位流水
    prefix = f"SO{order_date.strftime('%Y%m%d')}"
    count = db.query(SaleOrder).filter(
        SaleOrder.farm_id == farm_id, SaleOrder.order_no.like(f"{prefix}%")
    ).count()
    order_no = f"{prefix}{count + 1:03d}"

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
    for animal, weight in animals:
        costs = _calc_animal_cost(db, farm_id, animal, order_date)
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

        # 档案置已出栏 + 圈舍存栏减 1
        animal.status = "已出栏"
        animal.out_date = order_date
        if animal.pen_id:
            pen = db.query(Pen).filter(Pen.id == animal.pen_id).first()
            if pen and (pen.current_count or 0) > 0:
                pen.current_count -= 1

    order.animal_count = len(animals)
    order.total_weight = _round2(total_weight)
    order.total_amount = _round2(total_amount)
    db.commit()
    return order


def _calc_animal_cost(db: Session, farm_id: int, animal: Animal, out_date: date) -> dict:
    """计算单只饲养成本（DBD 8.2 sp_calc_animal_total_cost）"""
    in_date = animal.in_date or out_date
    raise_days = max((out_date - in_date).days, 0)

    # 饲料成本：所在圈舍饲喂记录成本累加（审核通过）
    feed_cost = 0
    if animal.pen_id:
        feed_cost = db.query(func.coalesce(func.sum(FeedingRecord.feed_cost), 0)).filter(
            FeedingRecord.farm_id == farm_id,
            FeedingRecord.pen_id == animal.pen_id,
            FeedingRecord.feed_date >= in_date,
            FeedingRecord.feed_date <= out_date,
            FeedingRecord.audit_status == "通过",
            FeedingRecord.deleted == False,
        ).scalar() or 0

    # 药品疫苗成本：当前物资表无单价，置 0（需物资单价支持后再精确分摊）
    medicine_cost = 0

    # 分摊人工成本：月均人工 × 饲养天数 / 30
    labor_cost = _avg_monthly_labor(db, farm_id) * raise_days / 30

    feed_cost = _round2(feed_cost)
    labor_cost = _round2(labor_cost)
    return {
        "raise_days": raise_days,
        "feed_cost": feed_cost,
        "medicine_cost": _round2(medicine_cost),
        "labor_cost": labor_cost,
        "consumable_cost": _round2(0),
        "total_cost": _round2(feed_cost + medicine_cost + labor_cost),
    }


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
                         growth_stage: Optional[str] = None, keyword: Optional[str] = None) -> List[Animal]:
    """出栏候选畜禽：在栏/待出栏的档案"""
    q = db.query(Animal).filter(
        Animal.farm_id == farm_id, Animal.status.in_(SALABLE_STATUSES), Animal.deleted == False
    )
    if species:
        q = q.filter(Animal.species == species)
    if growth_stage:
        q = q.filter(Animal.growth_stage == growth_stage)
    if keyword:
        q = q.filter(Animal.ear_tag.like(f"%{keyword}%"))
    return q.order_by(Animal.species, Animal.ear_tag).all()


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
    """时间段利润汇总：销售利润 - 成本支出 = 净利润"""
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
    total_amount = total_cost = total_profit = 0.0
    for detail in rows:
        order_ids.add(detail.order_id)
        animal_count += 1
        total_amount += float(detail.sale_amount or 0)
        total_cost += float(detail.total_cost or 0)
        total_profit += float(detail.profit or 0)

    eq = db.query(CostExpense).filter(CostExpense.farm_id == farm_id, CostExpense.deleted == False)
    if start_date:
        eq = eq.filter(CostExpense.expense_date >= start_date)
    if end_date:
        eq = eq.filter(CostExpense.expense_date <= end_date)
    expense_amount = sum(float(e.amount or 0) for e in eq.all())

    total_amount = _round2(total_amount)
    total_cost = _round2(total_cost)
    total_profit = _round2(total_profit)
    expense_amount = _round2(expense_amount)
    profit_rate = _round2(total_profit / total_amount * 100) if total_amount else 0
    return {
        "order_count": len(order_ids),
        "animal_count": animal_count,
        "total_amount": total_amount,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "profit_rate": profit_rate,
        "expense_amount": expense_amount,
        "net_profit": _round2(total_profit - expense_amount),
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
