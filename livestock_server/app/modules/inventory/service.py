"""
物资库存业务逻辑

核心业务规则：
1. 库存物资：同养殖场下，物资类型+名称唯一
2. 进货流程：员工提交进货记录（待审核）→ 场主审核通过 → 自动增加库存数量
   - 若库存里没有此物资，审核通过时自动创建一条库存记录
   - 若已有，则增加数量（并更新有效期/生产日期为最新进货批次的数据）
3. 领用流程：员工提交领用记录（待审核）→ 场主审核通过 → 自动扣减库存数量
   - 必须指定 stock_id
   - 库存不足时禁止审核通过（员工提交时也校验一次，但场主审核时再校验一次防并发）
4. 状态自动维护：每次查询库存时，根据 expiry_date 实时计算 status 和 is_shortage
   - 即将过期：有效期距今 ≤ 30 天且未过期
   - 已过期：有效期 < 今天
   - 缺货：库存数量 < 预警阈值
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.inventory.model import MaterialStock, MaterialPurchase, MaterialConsume
from app.modules.inventory.schema import (
    MaterialStockIn, MaterialStockUpdateIn, MaterialStockQuery,
    MaterialPurchaseIn, MaterialPurchaseUpdateIn, MaterialPurchaseQuery,
    MaterialConsumeIn, MaterialConsumeUpdateIn, MaterialConsumeQuery,
    AuditActionIn,
)

# 物资类型白名单
MATERIAL_TYPES = {"饲料", "疫苗", "兽药"}
# 即将过期阈值（天）
EXPIRY_WARNING_DAYS = 30


# ============================================================
# 库存物资
# ============================================================

def list_stock(db: Session, farm_id: int, query: MaterialStockQuery) -> dict:
    """库存列表（分页+筛选，实时计算 status 和 is_shortage）"""
    q = db.query(MaterialStock).filter(
        MaterialStock.farm_id == farm_id, MaterialStock.deleted == False
    )
    if query.material_type:
        q = q.filter(MaterialStock.material_type == query.material_type)
    if query.material_name:
        q = q.filter(MaterialStock.material_name.like(f"%{query.material_name}%"))
    if query.status:
        # 状态是动态算的，不能用 SQL 直接过滤，先取全部再内存过滤
        pass
    if query.is_shortage is not None:
        pass

    total = q.count()
    items = q.order_by(MaterialStock.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()

    # 实时刷新每条库存的 status 和 is_shortage
    for s in items:
        _refresh_stock_status(s)
        db.flush()

    # 内存过滤 status / is_shortage
    if query.status:
        items = [s for s in items if s.status == query.status]
    if query.is_shortage is not None:
        items = [s for s in items if s.is_shortage == query.is_shortage]
    # 如果做了内存过滤，总数需要重新算
    if query.status or query.is_shortage is not None:
        total = len(items)

    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_stock(db: Session, farm_id: int, stock_id: int) -> MaterialStock:
    s = db.query(MaterialStock).filter(
        MaterialStock.id == stock_id, MaterialStock.farm_id == farm_id, MaterialStock.deleted == False
    ).first()
    if not s:
        raise BizException("库存物资不存在", code=40050)
    _refresh_stock_status(s)
    return s


def add_stock(db: Session, farm_id: int, body: MaterialStockIn, user_id: int) -> MaterialStock:
    """新增库存物资"""
    if body.material_type not in MATERIAL_TYPES:
        raise BizException(f"物资类型只能是：{MATERIAL_TYPES}", code=40051)

    # 校验类型+名称唯一
    exists = db.query(MaterialStock).filter(
        MaterialStock.farm_id == farm_id,
        MaterialStock.material_type == body.material_type,
        MaterialStock.material_name == body.material_name,
        MaterialStock.deleted == False,
    ).first()
    if exists:
        raise BizException(f"{body.material_type}「{body.material_name}」已存在", code=40052)

    stock = MaterialStock(
        farm_id=farm_id,
        material_type=body.material_type,
        material_name=body.material_name,
        specification=body.specification,
        quantity=body.quantity,
        unit=body.unit,
        unit_price=body.unit_price,
        warning_threshold=body.warning_threshold,
        production_date=body.production_date,
        expiry_date=body.expiry_date,
        manager_user_id=body.manager_user_id,
        remark=body.remark,
    )
    _refresh_stock_status(stock)
    db.add(stock)
    db.commit()
    return stock


def update_stock(db: Session, farm_id: int, stock_id: int, body: MaterialStockUpdateIn) -> MaterialStock:
    s = get_stock(db, farm_id, stock_id)
    if body.specification is not None:
        s.specification = body.specification
    if body.unit is not None:
        s.unit = body.unit
    if body.unit_price is not None:
        s.unit_price = body.unit_price
    if body.warning_threshold is not None:
        s.warning_threshold = body.warning_threshold
    if body.production_date is not None:
        s.production_date = body.production_date
    if body.expiry_date is not None:
        s.expiry_date = body.expiry_date
    if body.manager_user_id is not None:
        s.manager_user_id = body.manager_user_id
    if body.remark is not None:
        s.remark = body.remark
    _refresh_stock_status(s)
    db.commit()
    return s


def delete_stock(db: Session, farm_id: int, stock_id: int):
    """删除库存（如果有未审核的进货/领用记录引用，禁止删除）"""
    s = get_stock(db, farm_id, stock_id)
    # 校验有无待审核的进货/领用记录引用
    pending_purchase = db.query(MaterialPurchase).filter(
        MaterialPurchase.stock_id == stock_id,
        MaterialPurchase.audit_status == "待审核",
        MaterialPurchase.deleted == False,
    ).count()
    pending_consume = db.query(MaterialConsume).filter(
        MaterialConsume.stock_id == stock_id,
        MaterialConsume.audit_status == "待审核",
        MaterialConsume.deleted == False,
    ).count()
    if pending_purchase or pending_consume:
        raise BizException(
            f"有 {pending_purchase + pending_consume} 条待审核记录引用此库存，不能删除",
            code=40053,
        )
    # 库存数量 > 0 时也提示一下（不强制禁止）
    if s.quantity and s.quantity > 0:
        raise BizException(f"当前库存还有 {s.quantity}{s.unit}，请先清零再删除", code=40054)
    s.deleted = True
    db.commit()


# ============================================================
# 进货
# ============================================================

def list_purchase(db: Session, farm_id: int, query: MaterialPurchaseQuery) -> dict:
    q = db.query(MaterialPurchase).filter(
        MaterialPurchase.farm_id == farm_id, MaterialPurchase.deleted == False
    )
    if query.material_type:
        q = q.filter(MaterialPurchase.material_type == query.material_type)
    if query.material_name:
        q = q.filter(MaterialPurchase.material_name.like(f"%{query.material_name}%"))
    if query.purchase_date_start:
        q = q.filter(MaterialPurchase.purchase_date >= query.purchase_date_start)
    if query.purchase_date_end:
        q = q.filter(MaterialPurchase.purchase_date <= query.purchase_date_end)
    if query.audit_status:
        q = q.filter(MaterialPurchase.audit_status == query.audit_status)

    total = q.count()
    items = q.order_by(MaterialPurchase.purchase_date.desc(), MaterialPurchase.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_purchase(db: Session, farm_id: int, purchase_id: int) -> MaterialPurchase:
    p = db.query(MaterialPurchase).filter(
        MaterialPurchase.id == purchase_id, MaterialPurchase.farm_id == farm_id, MaterialPurchase.deleted == False
    ).first()
    if not p:
        raise BizException("进货记录不存在", code=40060)
    return p


def add_purchase(db: Session, farm_id: int, body: MaterialPurchaseIn, user_id: int) -> MaterialPurchase:
    """员工提交进货记录（待审核，不立即增加库存）"""
    if body.material_type not in MATERIAL_TYPES:
        raise BizException(f"物资类型只能是：{MATERIAL_TYPES}", code=40051)

    # 自动算总金额
    total_cost = round(body.quantity * body.cost_price, 2)

    p = MaterialPurchase(
        farm_id=farm_id,
        stock_id=None,  # 审核通过时再关联
        material_type=body.material_type,
        material_name=body.material_name,
        batch_no=body.batch_no,
        quantity=body.quantity,
        unit=body.unit,
        cost_price=body.cost_price,
        total_cost=total_cost,
        production_date=body.production_date,
        expiry_date=body.expiry_date,
        supplier=body.supplier,
        purchase_date=body.purchase_date,
        audit_status="待审核",
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(p)
    db.commit()
    return p


def update_purchase(db: Session, farm_id: int, purchase_id: int, body: MaterialPurchaseUpdateIn) -> MaterialPurchase:
    """修改进货记录（仅待审核可改）"""
    p = get_purchase(db, farm_id, purchase_id)
    if p.audit_status != "待审核":
        raise BizException("已审核的记录不能修改", code=40061)

    if body.batch_no is not None:
        p.batch_no = body.batch_no
    if body.quantity is not None:
        p.quantity = body.quantity
    if body.unit is not None:
        p.unit = body.unit
    if body.cost_price is not None:
        p.cost_price = body.cost_price
    if body.production_date is not None:
        p.production_date = body.production_date
    if body.expiry_date is not None:
        p.expiry_date = body.expiry_date
    if body.supplier is not None:
        p.supplier = body.supplier
    if body.remark is not None:
        p.remark = body.remark

    # 重算总金额
    if p.quantity is not None and p.cost_price is not None:
        p.total_cost = round(float(p.quantity) * float(p.cost_price), 2)

    db.commit()
    return p


def delete_purchase(db: Session, farm_id: int, purchase_id: int):
    p = get_purchase(db, farm_id, purchase_id)
    if p.audit_status == "通过":
        raise BizException("已审核通过的记录不能删除", code=40062)
    p.deleted = True
    db.commit()


def audit_purchase(db: Session, farm_id: int, purchase_id: int, body: AuditActionIn) -> MaterialPurchase:
    """
    场主审核进货记录
    - 通过：自动关联/创建库存，并增加数量
    - 驳回：不动库存
    """
    if body.audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40063)

    p = get_purchase(db, farm_id, purchase_id)
    if p.audit_status != "待审核":
        raise BizException("该记录已审核，不能重复审核", code=40064)

    p.audit_status = body.audit_status
    if body.remark:
        p.remark = body.remark

    if body.audit_status == "通过":
        # 找库存（按 farm_id + 类型 + 名称）
        stock = db.query(MaterialStock).filter(
            MaterialStock.farm_id == farm_id,
            MaterialStock.material_type == p.material_type,
            MaterialStock.material_name == p.material_name,
            MaterialStock.deleted == False,
        ).first()

        if not stock:
            # 库存里没有，自动创建一条
            stock = MaterialStock(
                farm_id=farm_id,
                material_type=p.material_type,
                material_name=p.material_name,
                specification=None,
                quantity=0,
                unit=p.unit,
                unit_price=float(p.cost_price or 0),  # 首次建档直接取进货单价
                warning_threshold=None,
                production_date=p.production_date,
                expiry_date=p.expiry_date,
                status="正常",
                is_shortage=0,
            )
            db.add(stock)
            db.flush()

        # 增加库存数量
        old_qty = float(stock.quantity or 0)
        old_price = float(stock.unit_price or 0)
        in_qty = float(p.quantity)
        stock.quantity = old_qty + in_qty
        # 移动加权平均价：新均价 = (旧库存量×旧均价 + 本次进货量×进货单价) / 新库存量
        stock.unit_price = round((old_qty * old_price + in_qty * float(p.cost_price or 0)) / stock.quantity, 2)
        # 更新最新批次的有效期/生产日期
        if p.production_date:
            stock.production_date = p.production_date
        if p.expiry_date:
            stock.expiry_date = p.expiry_date
        # 关联 stock_id
        p.stock_id = stock.id
        # 刷新库存状态
        _refresh_stock_status(stock)

    db.commit()
    return p


# ============================================================
# 领用
# ============================================================

def list_consume(db: Session, farm_id: int, query: MaterialConsumeQuery) -> dict:
    q = db.query(MaterialConsume).filter(
        MaterialConsume.farm_id == farm_id, MaterialConsume.deleted == False
    )
    if query.material_type:
        q = q.filter(MaterialConsume.material_type == query.material_type)
    if query.material_name:
        q = q.filter(MaterialConsume.material_name.like(f"%{query.material_name}%"))
    if query.stock_id:
        q = q.filter(MaterialConsume.stock_id == query.stock_id)
    if query.consume_date_start:
        q = q.filter(MaterialConsume.consume_date >= query.consume_date_start)
    if query.consume_date_end:
        q = q.filter(MaterialConsume.consume_date <= query.consume_date_end)
    if query.audit_status:
        q = q.filter(MaterialConsume.audit_status == query.audit_status)
    if query.related_module:
        q = q.filter(MaterialConsume.related_module == query.related_module)

    total = q.count()
    items = q.order_by(MaterialConsume.consume_date.desc(), MaterialConsume.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_consume(db: Session, farm_id: int, consume_id: int) -> MaterialConsume:
    c = db.query(MaterialConsume).filter(
        MaterialConsume.id == consume_id, MaterialConsume.farm_id == farm_id, MaterialConsume.deleted == False
    ).first()
    if not c:
        raise BizException("领用记录不存在", code=40070)
    return c


def add_consume(db: Session, farm_id: int, body: MaterialConsumeIn, user_id: int) -> MaterialConsume:
    """员工提交领用记录（待审核，不立即扣库存，但校验库存是否充足）"""
    stock = db.query(MaterialStock).filter(
        MaterialStock.id == body.stock_id,
        MaterialStock.farm_id == farm_id,
        MaterialStock.deleted == False,
    ).first()
    if not stock:
        raise BizException("库存物资不存在", code=40071)

    # 校验库存充足（提交时校验一次）
    if float(stock.quantity or 0) < body.quantity:
        raise BizException(
            f"库存不足：当前 {stock.quantity}{stock.unit}，需领用 {body.quantity}{body.unit}",
            code=40072,
        )

    c = MaterialConsume(
        farm_id=farm_id,
        stock_id=body.stock_id,
        material_type=stock.material_type,
        material_name=stock.material_name,
        batch_no=body.batch_no,
        quantity=body.quantity,
        unit=body.unit,
        unit_price=float(stock.unit_price or 0),  # 单价快照，防止后续进货改价影响历史成本
        consume_date=body.consume_date,
        related_module=body.related_module,
        related_id=body.related_id,
        status="成功",
        audit_status="待审核",
        consumer_user_id=user_id,
        remark=body.remark,
    )
    db.add(c)
    db.commit()
    return c


def update_consume(db: Session, farm_id: int, consume_id: int, body: MaterialConsumeUpdateIn) -> MaterialConsume:
    """修改领用记录（仅待审核可改）"""
    c = get_consume(db, farm_id, consume_id)
    if c.audit_status != "待审核":
        raise BizException("已审核的记录不能修改", code=40073)

    if body.batch_no is not None:
        c.batch_no = body.batch_no
    if body.quantity is not None:
        # 重新校验库存
        stock = db.query(MaterialStock).filter(MaterialStock.id == c.stock_id).first()
        if stock and float(stock.quantity or 0) < body.quantity:
            raise BizException(
                f"库存不足：当前 {stock.quantity}{stock.unit}，需领用 {body.quantity}{body.unit}",
                code=40072,
            )
        c.quantity = body.quantity
    if body.unit is not None:
        c.unit = body.unit
    if body.consume_date is not None:
        c.consume_date = body.consume_date
    if body.related_module is not None:
        c.related_module = body.related_module
    if body.related_id is not None:
        c.related_id = body.related_id
    if body.remark is not None:
        c.remark = body.remark
    db.commit()
    return c


def delete_consume(db: Session, farm_id: int, consume_id: int):
    c = get_consume(db, farm_id, consume_id)
    if c.audit_status == "通过":
        raise BizException("已审核通过的记录不能删除", code=40074)
    c.deleted = True
    db.commit()


def audit_consume(db: Session, farm_id: int, consume_id: int, body: AuditActionIn) -> MaterialConsume:
    """
    场主审核领用记录
    - 通过：再次校验库存（防并发），扣减库存
    - 驳回：不动库存
    """
    if body.audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40075)

    c = get_consume(db, farm_id, consume_id)
    if c.audit_status != "待审核":
        raise BizException("该记录已审核，不能重复审核", code=40076)

    c.audit_status = body.audit_status
    if body.remark:
        c.remark = body.remark

    if body.audit_status == "通过":
        # 再次校验库存（防并发）
        stock = db.query(MaterialStock).filter(
            MaterialStock.id == c.stock_id, MaterialStock.farm_id == farm_id, MaterialStock.deleted == False
        ).first()
        if not stock:
            raise BizException("关联的库存物资已不存在", code=40077)
        if float(stock.quantity or 0) < float(c.quantity):
            raise BizException(
                f"库存不足，无法通过审核：当前 {stock.quantity}{stock.unit}，需领用 {c.quantity}{c.unit}",
                code=40072,
            )
        # 扣减库存
        stock.quantity = float(stock.quantity) - float(c.quantity)
        # 刷新状态
        _refresh_stock_status(stock)
        # 补单价快照（老数据可能为空；库存均价可能已被后续进货更新，按当前均价补齐）
        if c.unit_price is None:
            c.unit_price = float(stock.unit_price or 0)

    db.commit()
    return c


# ============================================================
# 内部工具
# ============================================================

def refresh_all_stock_status(db: Session) -> int:
    """刷新所有库存的过期/缺货状态（定时任务每日调用），返回状态发生变化的条数"""
    stocks = db.query(MaterialStock).filter(MaterialStock.deleted == False).all()
    changed = 0
    for s in stocks:
        old_status = s.status
        _refresh_stock_status(s)
        if s.status != old_status:
            changed += 1
    db.commit()
    return changed


def _refresh_stock_status(stock: MaterialStock):
    """
    实时刷新库存状态：
    - status: 正常 / 即将过期 / 已过期
    - is_shortage: 0 / 1
    """
    today = date.today()

    # 过期状态
    if stock.expiry_date:
        days_left = (stock.expiry_date - today).days
        if days_left < 0:
            stock.status = "已过期"
        elif days_left <= EXPIRY_WARNING_DAYS:
            stock.status = "即将过期"
        else:
            stock.status = "正常"
    else:
        stock.status = "正常"

    # 缺货状态
    if stock.warning_threshold is not None:
        stock.is_shortage = 1 if float(stock.quantity or 0) < float(stock.warning_threshold) else 0
    else:
        stock.is_shortage = 0
