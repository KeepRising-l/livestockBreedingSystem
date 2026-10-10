"""
销售财务路由

- 销售：出栏候选 → 出栏销售（自动算成本/利润）→ 订单列表/详情 → 结算
- 成本支出：CRUD
- 利润汇总：时间段销售利润 - 成本支出 = 净利润
- 薪资记录：按月生成 → 列表 → 发放

权限：仅养殖场主/超管（财务数据敏感，员工无权限）
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
from app.modules.finance import service as finance_service
from app.modules.finance.schema import (
    SaleOutIn, SaleOrderOut, SaleOrderDetailOut, SaleOrderQuery,
    CostExpenseIn, CostExpenseUpdateIn, CostExpenseOut, CostExpenseQuery,
    ProfitSummaryOut, SalaryGenerateIn, SalaryRecordOut, SalaryRecordQuery,
)

# 模块级权限：销售/成本/利润/薪资记录 均属「销售财务」模块，员工角色默认不含该模块
router = APIRouter(dependencies=[Depends(require_perms("finance"))])


def _check_owner(current_user: User):
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)


# ============================================================
# 出栏销售
# ============================================================

@router.get("/sale/candidates", summary="出栏候选畜禽列表（在栏/待出栏）")
def list_candidates(
    species: str = Query(None),
    growth_stage: str = Query(None),
    keyword: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_owner(current_user)
    animals = finance_service.list_sale_candidates(
        db, current_user.farm_id, species=species, growth_stage=growth_stage, keyword=keyword
    )
    data = [{
        "id": a.id, "ear_tag": a.ear_tag, "species": a.species, "breed": a.breed,
        "gender": a.gender, "pen_id": a.pen_id, "in_date": a.in_date,
        "growth_stage": a.growth_stage, "status": a.status,
    } for a in animals]
    return Result.ok(data=data)


@router.post("/sale/out", summary="出栏销售（自动算成本/利润，档案置已出栏）")
def sale_out(body: SaleOutIn, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    order = finance_service.sale_out(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=SaleOrderOut.model_validate(order),
                     msg=f"出栏销售成功，订单号 {order.order_no}")


@router.get("/sale/list", summary="销售订单列表（分页 + 多条件）")
def list_orders(
    order_no: str = Query(None), customer: str = Query(None),
    species: str = Query(None), settle_status: str = Query(None),
    start_date: date = Query(None), end_date: date = Query(None),
    pageNum: int = Query(1, ge=1), pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    _check_owner(current_user)
    query = SaleOrderQuery(order_no=order_no, customer=customer, species=species,
                           settle_status=settle_status, start_date=start_date, end_date=end_date,
                           pageNum=pageNum, pageSize=pageSize)
    result = finance_service.list_orders(db, current_user.farm_id, query)
    result["list"] = [SaleOrderOut.model_validate(o) for o in result["list"]]
    return Result.ok(data=result)


@router.get("/sale/{order_id}", summary="销售订单详情（含明细）")
def get_order(order_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    order, details = finance_service.get_order(db, current_user.farm_id, order_id)
    data = {
        **SaleOrderOut.model_validate(order).model_dump(),
        "details": [SaleOrderDetailOut.model_validate(d).model_dump() for d in details],
    }
    return Result.ok(data=data)


@router.post("/sale/settle/{order_id}", summary="结算销售订单")
def settle_order(order_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    order = finance_service.settle_order(db, current_user.farm_id, order_id)
    return Result.ok(data=SaleOrderOut.model_validate(order), msg="结算成功")


# ============================================================
# 成本支出
# ============================================================

@router.post("/expense/add", summary="新增成本支出")
def add_expense(body: CostExpenseIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    exp = finance_service.add_expense(db, current_user.farm_id, body)
    return Result.ok(data=CostExpenseOut.model_validate(exp), msg="新增成功")


@router.get("/expense/list", summary="成本支出列表（分页 + 类型/日期筛选）")
def list_expenses(
    expense_type: str = Query(None), start_date: date = Query(None), end_date: date = Query(None),
    pageNum: int = Query(1, ge=1), pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    _check_owner(current_user)
    query = CostExpenseQuery(expense_type=expense_type, start_date=start_date, end_date=end_date,
                             pageNum=pageNum, pageSize=pageSize)
    result = finance_service.list_expenses(db, current_user.farm_id, query)
    result["list"] = [CostExpenseOut.model_validate(e) for e in result["list"]]
    return Result.ok(data=result)


@router.put("/expense/{expense_id}", summary="修改成本支出")
def update_expense(expense_id: int, body: CostExpenseUpdateIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    exp = finance_service.update_expense(db, current_user.farm_id, expense_id, body)
    return Result.ok(data=CostExpenseOut.model_validate(exp), msg="修改成功")


@router.delete("/expense/{expense_id}", summary="删除成本支出")
def delete_expense(expense_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    finance_service.delete_expense(db, current_user.farm_id, expense_id)
    return Result.ok(msg="删除成功")


# ============================================================
# 利润汇总
# ============================================================

@router.get("/profit/summary", summary="利润汇总（销售利润 - 成本支出 = 净利润）")
def profit_summary(
    start_date: date = Query(None), end_date: date = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    _check_owner(current_user)
    data = finance_service.profit_summary(db, current_user.farm_id, start_date, end_date)
    return Result.ok(data=ProfitSummaryOut(**data))


# ============================================================
# 薪资记录
# ============================================================

@router.post("/salary/generate", summary="按月生成在职员工薪资记录")
def generate_salary(body: SalaryGenerateIn, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    created = finance_service.generate_salary(db, current_user.farm_id, body.pay_month)
    return Result.ok(data={"pay_month": body.pay_month, "created": created},
                     msg=f"{body.pay_month} 薪资生成完成，新增 {created} 条")


@router.get("/salary/list", summary="薪资记录列表（分页 + 月份/岗位/状态筛选）")
def list_salaries(
    pay_month: str = Query(None), post: str = Query(None), status: str = Query(None),
    pageNum: int = Query(1, ge=1), pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    _check_owner(current_user)
    query = SalaryRecordQuery(pay_month=pay_month, post=post, status=status,
                              pageNum=pageNum, pageSize=pageSize)
    result = finance_service.list_salaries(db, current_user.farm_id, query)
    result["list"] = [SalaryRecordOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.post("/salary/pay/{record_id}", summary="发放薪资（待发放 → 已发放）")
def pay_salary(record_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    rec = finance_service.pay_salary(db, current_user.farm_id, record_id)
    return Result.ok(data=SalaryRecordOut.model_validate(rec), msg="发放成功")
