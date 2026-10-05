"""
饲喂业务逻辑

核心业务规则：
1. 饲喂方案：场主配置，按畜种+生长阶段规定每只每次的精料/青贮/干草重量
2. 饲喂记录：员工提交，audit_status 自动 = 待审核；同一天同一圈舍同一时段不能重复
3. 投喂时根据所选方案自动填充 plan_xxx 字段（计划重量）
4. 饲喂成本：actual 重量 * 单价（从方案取）/ 1000（吨转 kg）
5. 审核流程：场主通过/驳回；通过后 status 才能置为已投喂
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.animal.model import Animal
from app.modules.feeding.model import FeedingPlan, FeedingRecord
from app.modules.pen.model import Pen
from app.modules.feeding.schema import (
    FeedingPlanIn, FeedingPlanUpdateIn, FeedingPlanQuery,
    FeedingRecordIn, FeedingRecordUpdateIn, FeedingRecordQuery,
    AuditActionIn,
)

# 支持的畜种编码
SPECIES_CODES = {"cattle": "牛", "sheep": "羊", "pig": "猪"}


# ============================================================
# 饲喂方案
# ============================================================

def list_plans(db: Session, farm_id: int, query: FeedingPlanQuery) -> dict:
    """方案列表（分页+筛选）"""
    q = db.query(FeedingPlan).filter(
        FeedingPlan.farm_id == farm_id, FeedingPlan.deleted == False
    )
    if query.species:
        q = q.filter(FeedingPlan.species == query.species)
    if query.applicable_stage:
        q = q.filter(FeedingPlan.applicable_stage == query.applicable_stage)
    if query.status is not None:
        q = q.filter(FeedingPlan.status == query.status)

    total = q.count()
    items = q.order_by(FeedingPlan.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_plan(db: Session, farm_id: int, plan_id: int) -> FeedingPlan:
    plan = db.query(FeedingPlan).filter(
        FeedingPlan.id == plan_id, FeedingPlan.farm_id == farm_id, FeedingPlan.deleted == False
    ).first()
    if not plan:
        raise BizException("饲喂方案不存在", code=40030)
    return plan


def add_plan(db: Session, farm_id: int, body: FeedingPlanIn, user_id: int) -> FeedingPlan:
    """新增方案"""
    if body.species not in SPECIES_CODES:
        raise BizException(f"不支持的畜种编码：{body.species}，应为 cattle/sheep/pig", code=40031)

    # 校验方案名唯一
    exists = db.query(FeedingPlan).filter(
        FeedingPlan.farm_id == farm_id,
        FeedingPlan.plan_name == body.plan_name,
        FeedingPlan.deleted == False,
    ).first()
    if exists:
        raise BizException("方案名称已存在", code=40032)

    # 算预计单只日成本 = 各类饲料(重量*次数) * 单价 / 1000（吨转kg）
    est_cost = _calc_est_cost_per_day(
        body.feed_times_per_day,
        body.concentrate_weight, body.concentrate_price,
        body.silage_weight, body.silage_price,
        body.hay_weight, body.hay_price,
    )

    plan = FeedingPlan(
        farm_id=farm_id,
        species=body.species,
        plan_name=body.plan_name,
        applicable_stage=body.applicable_stage,
        applicable_pen_type=body.applicable_pen_type,
        feed_times_per_day=body.feed_times_per_day,
        concentrate_weight=body.concentrate_weight,
        silage_weight=body.silage_weight,
        hay_weight=body.hay_weight,
        concentrate_price=body.concentrate_price,
        silage_price=body.silage_price,
        hay_price=body.hay_price,
        est_cost_per_day=est_cost,
        status=1,
        remark=body.remark,
    )
    db.add(plan)
    db.commit()
    return plan


def update_plan(db: Session, farm_id: int, plan_id: int, body: FeedingPlanUpdateIn) -> FeedingPlan:
    plan = get_plan(db, farm_id, plan_id)

    # 改名时校验唯一
    if body.plan_name and body.plan_name != plan.plan_name:
        exists = db.query(FeedingPlan).filter(
            FeedingPlan.farm_id == farm_id,
            FeedingPlan.plan_name == body.plan_name,
            FeedingPlan.deleted == False,
        ).first()
        if exists:
            raise BizException("方案名称已存在", code=40032)
        plan.plan_name = body.plan_name

    if body.applicable_stage is not None:
        plan.applicable_stage = body.applicable_stage
    if body.applicable_pen_type is not None:
        plan.applicable_pen_type = body.applicable_pen_type
    if body.feed_times_per_day is not None:
        plan.feed_times_per_day = body.feed_times_per_day
    if body.concentrate_weight is not None:
        plan.concentrate_weight = body.concentrate_weight
    if body.silage_weight is not None:
        plan.silage_weight = body.silage_weight
    if body.hay_weight is not None:
        plan.hay_weight = body.hay_weight
    if body.concentrate_price is not None:
        plan.concentrate_price = body.concentrate_price
    if body.silage_price is not None:
        plan.silage_price = body.silage_price
    if body.hay_price is not None:
        plan.hay_price = body.hay_price
    if body.status is not None:
        plan.status = body.status
    if body.remark is not None:
        plan.remark = body.remark

    # 重新算预计单只日成本
    plan.est_cost_per_day = _calc_est_cost_per_day(
        plan.feed_times_per_day,
        plan.concentrate_weight, plan.concentrate_price,
        plan.silage_weight, plan.silage_price,
        plan.hay_weight, plan.hay_price,
    )
    db.commit()
    return plan


def delete_plan(db: Session, farm_id: int, plan_id: int):
    plan = get_plan(db, farm_id, plan_id)
    # 校验有没有饲喂记录引用，有的话不允许删
    ref_count = db.query(FeedingRecord).filter(
        FeedingRecord.plan_id == plan_id,
        FeedingRecord.deleted == False,
    ).count()
    if ref_count > 0:
        raise BizException(f"有 {ref_count} 条饲喂记录引用此方案，不能删除", code=40033)
    plan.deleted = True
    db.commit()


# ============================================================
# 饲喂记录
# ============================================================

def list_records(db: Session, farm_id: int, query: FeedingRecordQuery) -> dict:
    """记录列表（分页+多条件）"""
    q = db.query(FeedingRecord).filter(
        FeedingRecord.farm_id == farm_id, FeedingRecord.deleted == False
    )
    if query.species:
        # 只返回圈养了该畜种畜禽的圈舍的饲喂记录
        pen_rows = db.query(Animal.pen_id).filter(
            Animal.farm_id == farm_id, Animal.species == query.species, Animal.deleted == False
        ).distinct().all()
        ids = [r[0] for r in pen_rows if r[0] is not None]
        q = q.filter(FeedingRecord.pen_id.in_(ids) if ids else False)
    if query.feed_date_start:
        q = q.filter(FeedingRecord.feed_date >= query.feed_date_start)
    if query.feed_date_end:
        q = q.filter(FeedingRecord.feed_date <= query.feed_date_end)
    if query.pen_id:
        q = q.filter(FeedingRecord.pen_id == query.pen_id)
    if query.time_period:
        q = q.filter(FeedingRecord.time_period == query.time_period)
    if query.audit_status:
        q = q.filter(FeedingRecord.audit_status == query.audit_status)
    if query.status:
        q = q.filter(FeedingRecord.status == query.status)

    total = q.count()
    items = q.order_by(FeedingRecord.feed_date.desc(), FeedingRecord.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_record(db: Session, farm_id: int, record_id: int) -> FeedingRecord:
    rec = db.query(FeedingRecord).filter(
        FeedingRecord.id == record_id, FeedingRecord.farm_id == farm_id, FeedingRecord.deleted == False
    ).first()
    if not rec:
        raise BizException("饲喂记录不存在", code=40040)
    return rec


def add_record(db: Session, farm_id: int, body: FeedingRecordIn, user_id: int) -> FeedingRecord:
    """
    员工新增饲喂记录。
    - 校验圈舍归属
    - 校验同日同时段同圈舍不重复
    - 选了方案：自动填充 plan_xxx 字段
    - audit_status 固定为 待审核
    """
    # 校验圈舍
    pen = db.query(Pen).filter(
        Pen.id == body.pen_id, Pen.farm_id == farm_id, Pen.deleted == False
    ).first()
    if not pen:
        raise BizException("圈舍不存在", code=40041)

    # 校验同日同时段同圈舍不重复
    exists = db.query(FeedingRecord).filter(
        FeedingRecord.farm_id == farm_id,
        FeedingRecord.feed_date == body.feed_date,
        FeedingRecord.time_period == body.time_period,
        FeedingRecord.pen_id == body.pen_id,
        FeedingRecord.deleted == False,
    ).first()
    if exists:
        raise BizException(
            f"{body.feed_date} {body.time_period} 时段 圈舍ID={body.pen_id} 已有饲喂记录",
            code=40042,
        )

    plan_concentrate = plan_silage = plan_hay = None
    plan = None
    if body.plan_id:
        plan = get_plan(db, farm_id, body.plan_id)
        plan_concentrate = plan.concentrate_weight
        plan_silage = plan.silage_weight
        plan_hay = plan.hay_weight

    # 算实际成本：按 actual 重量 + 方案单价
    feed_cost = _calc_feed_cost(
        body.actual_concentrate, plan.concentrate_price if plan else None,
        body.actual_silage, plan.silage_price if plan else None,
        body.actual_hay, plan.hay_price if plan else None,
    )

    rec = FeedingRecord(
        farm_id=farm_id,
        feed_date=body.feed_date,
        time_period=body.time_period,
        pen_id=body.pen_id,
        pen_type=pen.pen_type,
        plan_id=body.plan_id,
        plan_concentrate=plan_concentrate,
        plan_silage=plan_silage,
        plan_hay=plan_hay,
        actual_concentrate=body.actual_concentrate,
        actual_silage=body.actual_silage,
        actual_hay=body.actual_hay,
        animal_count=body.animal_count,
        feed_cost=feed_cost,
        status=body.status,
        audit_status="待审核",  # 员工提交固定进待审核
        operator_user_id=user_id,
        feed_time=datetime.now() if body.status == "已投喂" else None,
        remark=body.remark,
    )
    db.add(rec)
    db.commit()
    return rec


def update_record(db: Session, farm_id: int, record_id: int, body: FeedingRecordUpdateIn) -> FeedingRecord:
    """
    修改饲喂记录。
    - 待审核：直接改，状态保持待审核
    - 已通过/已驳回：允许修改（不改变投喂日期/时段/圈舍），改完 audit_status 重置回 待审核，
      需场主重新审核（审核不影响库存，重置只是让改动重新过一遍确认）
    """
    rec = get_record(db, farm_id, record_id)
    was_audited = rec.audit_status != "待审核"

    if body.actual_concentrate is not None:
        rec.actual_concentrate = body.actual_concentrate
    if body.actual_silage is not None:
        rec.actual_silage = body.actual_silage
    if body.actual_hay is not None:
        rec.actual_hay = body.actual_hay
    if body.animal_count is not None:
        rec.animal_count = body.animal_count
    if body.status is not None:
        rec.status = body.status
        if body.status == "已投喂":
            rec.feed_time = datetime.now()
    if body.remark is not None:
        rec.remark = body.remark

    # 重算成本
    plan = db.query(FeedingPlan).filter(FeedingPlan.id == rec.plan_id).first() if rec.plan_id else None
    rec.feed_cost = _calc_feed_cost(
        rec.actual_concentrate, plan.concentrate_price if plan else None,
        rec.actual_silage, plan.silage_price if plan else None,
        rec.actual_hay, plan.hay_price if plan else None,
    )
    if was_audited:
        rec.audit_status = "待审核"
    db.commit()
    return rec


def delete_record(db: Session, farm_id: int, record_id: int):
    rec = get_record(db, farm_id, record_id)
    if rec.audit_status == "通过":
        raise BizException("已审核通过的记录不能删除", code=40044)
    rec.deleted = True
    db.commit()


def audit_record(db: Session, farm_id: int, record_id: int, body: AuditActionIn) -> FeedingRecord:
    """
    场主审核饲喂记录
    - 通过：audit_status=通过，status 自动置为已投喂
    - 驳回：audit_status=驳回
    """
    if body.audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40045)

    rec = get_record(db, farm_id, record_id)
    if rec.audit_status != "待审核":
        raise BizException("该记录已审核，不能重复审核", code=40046)

    rec.audit_status = body.audit_status
    if body.audit_status == "通过":
        rec.status = "已投喂"
        rec.feed_time = datetime.now()
    if body.remark:
        rec.remark = body.remark
    db.commit()
    return rec


# ============================================================
# 内部工具函数
# ============================================================

def _calc_est_cost_per_day(
    times_per_day: int,
    c_weight, c_price,
    s_weight, s_price,
    h_weight, h_price,
) -> Optional[float]:
    """
    计算预计单只日成本（元）
    公式：Σ(每次重量 * 每日次数 * 单价) / 1000  （重量单位 kg，单价元/吨）
    注意：参数可能是 float、int、Decimal 混合，统一转 float 计算
    """
    has_data = any([c_weight, s_weight, h_weight]) and any([c_price, s_price, h_price])
    if not has_data:
        return None

    def to_f(x):
        return float(x) if x is not None else 0.0

    total = 0.0
    if c_weight and c_price:
        total += to_f(c_weight) * times_per_day * to_f(c_price) / 1000
    if s_weight and s_price:
        total += to_f(s_weight) * times_per_day * to_f(s_price) / 1000
    if h_weight and h_price:
        total += to_f(h_weight) * times_per_day * to_f(h_price) / 1000
    return round(total, 2)


def _calc_feed_cost(
    actual_c, c_price,
    actual_s, s_price,
    actual_h, h_price,
) -> Optional[float]:
    """
    计算本次饲喂成本（元）
    用实际投喂重量 * 方案里配置的单价 / 1000（吨转kg）
    """
    has_data = any([actual_c, actual_s, actual_h])
    if not has_data:
        return None

    def to_f(x):
        return float(x) if x is not None else 0.0

    total = 0.0
    if actual_c and c_price:
        total += to_f(actual_c) * to_f(c_price) / 1000
    if actual_s and s_price:
        total += to_f(actual_s) * to_f(s_price) / 1000
    if actual_h and h_price:
        total += to_f(actual_h) * to_f(h_price) / 1000
    return round(total, 2) if total > 0 else None
