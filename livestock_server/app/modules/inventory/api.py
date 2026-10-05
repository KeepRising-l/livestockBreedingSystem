"""
物资库存路由

- 库存 CRUD：场主/超管能增删改，员工只能查看
- 进货/领用记录：员工可提交（待审核），审核只能场主/超管
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.perms import require_perms
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.inventory.schema import (
    MaterialStockIn, MaterialStockIncreaseIn, MaterialStockUpdateIn, MaterialStockOut, MaterialStockQuery,
    MaterialPurchaseIn, MaterialPurchaseUpdateIn, MaterialPurchaseOut, MaterialPurchaseQuery,
    MaterialConsumeIn, MaterialConsumeUpdateIn, MaterialConsumeOut, MaterialConsumeQuery,
    AuditActionIn,
)
from app.modules.inventory import service as inventory_service

router = APIRouter(dependencies=[Depends(require_perms("inventory"))])


def _check_manager(current_user: User):
    """库存管理权限：场主或超管"""
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)


# ============================================================
# 库存物资
# ============================================================

@router.get("/stock/list", summary="库存列表")
def list_stock(
    material_type: str = Query(None, description="物资类型：饲料/疫苗/兽药"),
    material_name: str = Query(None),
    status: str = Query(None, description="状态：正常/即将过期/已过期"),
    is_shortage: int = Query(None, description="是否缺货：0否 1是"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = MaterialStockQuery(
        material_type=material_type, material_name=material_name,
        status=status, is_shortage=is_shortage,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = inventory_service.list_stock(db, current_user.farm_id, query)
    result["list"] = [MaterialStockOut.model_validate(s) for s in result["list"]]
    return Result.ok(data=result)


@router.get("/stock/{stock_id}", summary="库存详情")
def get_stock(stock_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    s = inventory_service.get_stock(db, current_user.farm_id, stock_id)
    return Result.ok(data=MaterialStockOut.model_validate(s))


@router.post("/stock/add", summary="新增库存物资")
def add_stock(body: MaterialStockIn, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    _check_manager(current_user)
    s = inventory_service.add_stock(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=MaterialStockOut.model_validate(s), msg="添加成功")


@router.post("/stock/increase", summary="增加库存（管理端免审直接入库）")
def increase_stock(body: MaterialStockIncreaseIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    _check_manager(current_user)
    p = inventory_service.increase_stock(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=MaterialPurchaseOut.model_validate(p), msg="入库成功")


@router.put("/stock/update/{stock_id}", summary="修改库存物资")
def update_stock(stock_id: int, body: MaterialStockUpdateIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _check_manager(current_user)
    s = inventory_service.update_stock(db, current_user.farm_id, stock_id, body)
    return Result.ok(data=MaterialStockOut.model_validate(s), msg="修改成功")


@router.delete("/stock/{stock_id}", summary="删除库存物资")
def delete_stock(stock_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _check_manager(current_user)
    inventory_service.delete_stock(db, current_user.farm_id, stock_id)
    return Result.ok(msg="删除成功")


# ============================================================
# 进货
# ============================================================

@router.get("/purchase/list", summary="进货记录列表")
def list_purchase(
    material_type: str = Query(None),
    material_name: str = Query(None),
    purchase_date_start: date = Query(None),
    purchase_date_end: date = Query(None),
    audit_status: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = MaterialPurchaseQuery(
        material_type=material_type, material_name=material_name,
        purchase_date_start=purchase_date_start, purchase_date_end=purchase_date_end,
        audit_status=audit_status, pageNum=pageNum, pageSize=pageSize,
    )
    result = inventory_service.list_purchase(db, current_user.farm_id, query)
    result["list"] = [MaterialPurchaseOut.model_validate(p) for p in result["list"]]
    return Result.ok(data=result)


@router.get("/purchase/{purchase_id}", summary="进货记录详情")
def get_purchase(purchase_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    p = inventory_service.get_purchase(db, current_user.farm_id, purchase_id)
    return Result.ok(data=MaterialPurchaseOut.model_validate(p))


@router.post("/purchase/add", summary="提交进货记录（待审核）")
def add_purchase(body: MaterialPurchaseIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    p = inventory_service.add_purchase(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=MaterialPurchaseOut.model_validate(p), msg="提交成功，等待审核")


@router.put("/purchase/update/{purchase_id}", summary="修改进货记录（仅待审核）")
def update_purchase(purchase_id: int, body: MaterialPurchaseUpdateIn, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    p = inventory_service.update_purchase(db, current_user.farm_id, purchase_id, body)
    return Result.ok(data=MaterialPurchaseOut.model_validate(p), msg="修改成功")


@router.delete("/purchase/{purchase_id}", summary="删除进货记录（已通过不能删）")
def delete_purchase(purchase_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    inventory_service.delete_purchase(db, current_user.farm_id, purchase_id)
    return Result.ok(msg="删除成功")


@router.post("/purchase/audit/{purchase_id}", summary="审核进货记录（场主权限）")
def audit_purchase(purchase_id: int, body: AuditActionIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    _check_manager(current_user)
    p = inventory_service.audit_purchase(db, current_user.farm_id, purchase_id, body)
    return Result.ok(data=MaterialPurchaseOut.model_validate(p), msg=f"已{body.audit_status}")


# ============================================================
# 领用
# ============================================================

@router.get("/consume/list", summary="领用记录列表")
def list_consume(
    material_type: str = Query(None),
    material_name: str = Query(None),
    stock_id: int = Query(None),
    consume_date_start: date = Query(None),
    consume_date_end: date = Query(None),
    audit_status: str = Query(None),
    related_module: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = MaterialConsumeQuery(
        material_type=material_type, material_name=material_name, stock_id=stock_id,
        consume_date_start=consume_date_start, consume_date_end=consume_date_end,
        audit_status=audit_status, related_module=related_module,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = inventory_service.list_consume(db, current_user.farm_id, query)
    result["list"] = [MaterialConsumeOut.model_validate(c) for c in result["list"]]
    return Result.ok(data=result)


@router.get("/consume/{consume_id}", summary="领用记录详情")
def get_consume(consume_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    c = inventory_service.get_consume(db, current_user.farm_id, consume_id)
    return Result.ok(data=MaterialConsumeOut.model_validate(c))


@router.post("/consume/add", summary="提交领用记录（待审核）")
def add_consume(body: MaterialConsumeIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    c = inventory_service.add_consume(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=MaterialConsumeOut.model_validate(c), msg="提交成功，等待审核")


@router.put("/consume/update/{consume_id}", summary="修改领用记录（仅待审核）")
def update_consume(consume_id: int, body: MaterialConsumeUpdateIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    c = inventory_service.update_consume(db, current_user.farm_id, consume_id, body)
    return Result.ok(data=MaterialConsumeOut.model_validate(c), msg="修改成功")


@router.delete("/consume/{consume_id}", summary="删除领用记录（已通过不能删）")
def delete_consume(consume_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    inventory_service.delete_consume(db, current_user.farm_id, consume_id)
    return Result.ok(msg="删除成功")


@router.post("/consume/audit/{consume_id}", summary="审核领用记录（场主权限）")
def audit_consume(consume_id: int, body: AuditActionIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _check_manager(current_user)
    c = inventory_service.audit_consume(db, current_user.farm_id, consume_id, body)
    return Result.ok(data=MaterialConsumeOut.model_validate(c), msg=f"已{body.audit_status}")
