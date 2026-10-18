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
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.models.user import User
from app.modules.inventory.model import MaterialStock, MaterialPurchase, MaterialConsume
from app.modules.inventory.schema import (
    MaterialStockIn, MaterialStockIncreaseIn, MaterialStockUpdateIn, MaterialStockQuery,
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
    # status / is_shortage 是派生状态，但推导规则固定，可以直接下推到 SQL 过滤，保证分页正确
    today = date.today()
    warn_date = today + timedelta(days=EXPIRY_WARNING_DAYS)
    if query.status:
        if query.status == "已过期":
            q = q.filter(MaterialStock.expiry_date < today)
        elif query.status == "即将过期":
            q = q.filter(MaterialStock.expiry_date >= today, MaterialStock.expiry_date <= warn_date)
        elif query.status == "正常":
            q = q.filter(
                (MaterialStock.expiry_date.is_(None)) | (MaterialStock.expiry_date > warn_date)
            )
    if query.is_shortage is not None:
        if query.is_shortage == 1:
            q = q.filter(
                MaterialStock.warning_threshold.isnot(None),
                MaterialStock.quantity < MaterialStock.warning_threshold,
            )
        else:
            q = q.filter(
                (MaterialStock.warning_threshold.is_(None))
                | (MaterialStock.quantity >= MaterialStock.warning_threshold)
            )

    total = q.count()
    items = q.order_by(MaterialStock.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()

    # 实时刷新每条库存的 status 和 is_shortage
    for s in items:
        _refresh_stock_status(s)
        db.flush()

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


def increase_stock(db: Session, farm_id: int, body: MaterialStockIncreaseIn, user_id: int) -> MaterialPurchase:
    """管理端增加库存（免审）：落一条 audit_status=通过 的进货记录作为同步依据，并立即同步库存。
    与员工进货共用同一段同步逻辑，库存变化全系统只有一条路径。"""
    if body.material_type not in MATERIAL_TYPES:
        raise BizException(f"物资类型只能是：{MATERIAL_TYPES}", code=40051)

    p = MaterialPurchase(
        farm_id=farm_id,
        stock_id=None,
        material_type=body.material_type,
        material_name=body.material_name,
        batch_no=body.batch_no,
        quantity=body.quantity,
        unit=body.unit,
        # cost_price 列 NOT NULL：不填时落 0 表示"未提供单价"，同步时会跳过均价更新
        cost_price=body.cost_price or 0,
        total_cost=round(body.quantity * body.cost_price, 2) if body.cost_price else None,
        production_date=body.production_date,
        expiry_date=body.expiry_date,
        supplier=body.supplier,
        purchase_date=body.purchase_date,
        audit_status="通过",  # 管理端免审，直接通过
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(p)
    db.flush()
    _sync_purchase_to_stock(db, farm_id, p)
    db.commit()
    return p


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
    场主审核进货记录（并发安全）
    - 先用条件更新原子地把 待审核 → 通过/驳回：同一单据并发审核只有一个请求成功
    - 通过：自动关联/创建库存并增加数量（_sync_purchase_to_stock 内部带行锁）
    - 驳回：不动库存
    - 状态迁移与库存变更在同一事务中提交，任一环节失败整体回滚
    """
    if body.audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40063)

    p = get_purchase(db, farm_id, purchase_id)
    if p.audit_status != "待审核":
        raise BizException("该记录已审核，不能重复审核", code=40064)

    # 原子状态迁移：只允许 待审核 → 终态 一次，并发重复审核在此被拦截
    moved = db.execute(
        update(MaterialPurchase)
        .where(
            MaterialPurchase.id == purchase_id,
            MaterialPurchase.farm_id == farm_id,
            MaterialPurchase.deleted == False,
            MaterialPurchase.audit_status == "待审核",
        )
        .values(audit_status=body.audit_status)
        .execution_options(synchronize_session="evaluate")
    )
    if moved.rowcount == 0:
        raise BizException("该记录已审核，不能重复审核", code=40064)

    if body.remark:
        p.remark = body.remark

    if body.audit_status == "通过":
        _sync_purchase_to_stock(db, farm_id, p)

    db.commit()
    return p


def _lock_stock(db: Session, farm_id: int, material_type: str, material_name: str,
                include_deleted: bool = False) -> Optional[MaterialStock]:
    """
    按 (farm_id, 物资类型, 名称) 查库存行并加行锁（SELECT ... FOR UPDATE）。

    - MySQL/InnoDB 下锁定该行直到事务提交，防止并发进货/入库丢失更新；
      行锁读总是读取最新已提交版本，并发创建冲突后的重查也能看到对手已提交的行
    - SQLite 方言会忽略 FOR UPDATE（单写者模型，测试场景退化为普通查询）
    - include_deleted=True 时连软删除的行一并返回（唯一键 uk_farm_type_name
      覆盖软删行，插入冲突后需要用它复活记录）
    """
    q = db.query(MaterialStock).filter(
        MaterialStock.farm_id == farm_id,
        MaterialStock.material_type == material_type,
        MaterialStock.material_name == material_name,
    )
    if not include_deleted:
        q = q.filter(MaterialStock.deleted == False)
    return q.with_for_update().first()


def _sync_purchase_to_stock(db: Session, farm_id: int, p: MaterialPurchase):
    """
    进货记录同步库存（全系统唯一入口，并发安全）：
    1. 行锁锁定 (farm_id, 类型, 名称) 对应库存，没有则自动建档；
       并发创建撞唯一键 uk_farm_type_name 时回滚保存点后重查。
       若冲突行是此前软删除的同名库存（删除前要求数量清零），复活并继续累加，
       不再出现未处理的 500。
    2. 数量累加进货数量
    3. 有进货单价则移动加权更新均价，无单价则保持原价
    4. 生产日期/有效期更新为最新批次
    5. 回填 stock_id 并刷新过期/缺货状态
    """
    stock = _lock_stock(db, farm_id, p.material_type, p.material_name)

    if not stock:
        try:
            with db.begin_nested():
                stock = MaterialStock(
                    farm_id=farm_id,
                    material_type=p.material_type,
                    material_name=p.material_name,
                    specification=None,
                    quantity=0,
                    unit=p.unit,
                    unit_price=float(p.cost_price) if p.cost_price else None,
                    warning_threshold=None,
                    production_date=p.production_date,
                    expiry_date=p.expiry_date,
                    status="正常",
                    is_shortage=0,
                )
                db.add(stock)
                db.flush()
        except IntegrityError:
            # 并发对手已提交同 (farm_id, 类型, 名称) 的库存行，或撞上软删除的同名行：
            # 回滚保存点后带行锁重查（含软删行），命中则继续在既有行上累加/复活
            stock = _lock_stock(db, farm_id, p.material_type, p.material_name, include_deleted=True)
            if stock is None:
                raise
            stock.deleted = False

    # 增加库存数量
    old_qty = float(stock.quantity or 0)
    in_qty = float(p.quantity)
    stock.quantity = old_qty + in_qty
    # 移动加权平均价：新均价 = (旧库存量×旧均价 + 本次进货量×进货单价) / 新库存量；无单价则不动均价
    if p.cost_price:
        old_price = float(stock.unit_price or 0)
        stock.unit_price = round((old_qty * old_price + in_qty * float(p.cost_price)) / stock.quantity, 2)
    # 更新最新批次的有效期/生产日期
    if p.production_date:
        stock.production_date = p.production_date
    if p.expiry_date:
        stock.expiry_date = p.expiry_date
    # 关联 stock_id
    p.stock_id = stock.id
    # 刷新库存状态
    _refresh_stock_status(stock)


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
    _attach_consumer_names(db, items)
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_consume(db: Session, farm_id: int, consume_id: int) -> MaterialConsume:
    c = db.query(MaterialConsume).filter(
        MaterialConsume.id == consume_id, MaterialConsume.farm_id == farm_id, MaterialConsume.deleted == False
    ).first()
    if not c:
        raise BizException("领用记录不存在", code=40070)
    _attach_consumer_names(db, [c])
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
    场主审核领用记录（并发安全）
    - 先用条件更新原子地把 待审核 → 通过/驳回：同一单据并发审核只有一个请求成功
    - 通过：行锁锁定库存行后再次校验并扣减，库存不足抛错时整个事务回滚
      （单据状态不会单独落库，不会出现"审核通过但没扣库存"的中间态）
    - 驳回：不动库存
    """
    if body.audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40075)

    c = get_consume(db, farm_id, consume_id)
    if c.audit_status != "待审核":
        raise BizException("该记录已审核，不能重复审核", code=40076)

    # 原子状态迁移：只允许 待审核 → 终态 一次，并发重复审核在此被拦截
    moved = db.execute(
        update(MaterialConsume)
        .where(
            MaterialConsume.id == consume_id,
            MaterialConsume.farm_id == farm_id,
            MaterialConsume.deleted == False,
            MaterialConsume.audit_status == "待审核",
        )
        .values(audit_status=body.audit_status)
        .execution_options(synchronize_session="evaluate")
    )
    if moved.rowcount == 0:
        raise BizException("该记录已审核，不能重复审核", code=40076)

    if body.remark:
        c.remark = body.remark

    if body.audit_status == "通过":
        # 行锁读库存（MySQL/InnoDB SELECT..FOR UPDATE，锁到事务提交；SQLite 方言忽略）
        stock = db.query(MaterialStock).filter(
            MaterialStock.id == c.stock_id, MaterialStock.farm_id == farm_id, MaterialStock.deleted == False
        ).with_for_update().first()
        if not stock:
            raise BizException("关联的库存物资已不存在", code=40077)
        if float(stock.quantity or 0) < float(c.quantity):
            raise BizException(
                f"库存不足，无法通过审核：当前 {stock.quantity}{stock.unit}，需领用 {c.quantity}{c.unit}",
                code=40072,
            )
        # 扣减库存（行锁保护下不会扣成负数）
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


def _attach_consumer_names(db: Session, items: list):
    """给领用记录动态挂上领用人姓名（= consumer_user_id 对应用户 real_name），仅用于展示"""
    ids = {c.consumer_user_id for c in items if c.consumer_user_id}
    if not ids:
        return
    users = db.query(User.id, User.real_name).filter(User.id.in_(ids)).all()
    name_map = {u.id: u.real_name for u in users}
    for c in items:
        c.consumer_name = name_map.get(c.consumer_user_id)


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
