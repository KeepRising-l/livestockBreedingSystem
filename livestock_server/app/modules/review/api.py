"""
审核路由

- counts：各类型待审核数量（供前端 tab 角标）
- list：单类型待审核列表（分页）
- pending：全部待审核（聚合，按时间倒序）
- audit：统一审核（通过/驳回），仅场主/超管可执行
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.perms import require_perms
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.review import service as review_service
from app.modules.review.schema import ReviewAuditIn, ReviewBatchAuditIn, ReviewItemOut

# 模块级权限：审核是场主职责，员工角色默认不含该模块
router = APIRouter(dependencies=[Depends(require_perms("review"))])


def _require_farm(current_user: User) -> int:
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    return current_user.farm_id


def _check_owner(current_user: User):
    """审核仅养殖场主/超管"""
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)


@router.get("/counts", summary="各类型待审核数量统计")
def get_counts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    farm_id = _require_farm(current_user)
    return Result.ok(data=review_service.counts(db, farm_id))


@router.get("/list", summary="单类型待审核列表（分页）")
def list_pending(
    business_type: str = Query(..., description="feeding/purchase/consume/vaccine/medical"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    result = review_service.list_pending(db, farm_id, business_type, pageNum, pageSize)
    result["list"] = [ReviewItemOut.model_validate(it) for it in result["list"]]
    return Result.ok(data=result)


@router.get("/pending", summary="全部待审核（聚合各类型，按时间倒序）")
def list_all_pending(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm_id = _require_farm(current_user)
    result = review_service.list_all_pending(db, farm_id, limit)
    result["list"] = [ReviewItemOut.model_validate(it) for it in result["list"]]
    return Result.ok(data=result)


@router.post("/audit", summary="统一审核（场主/超管权限）")
def audit_record(body: ReviewAuditIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    result = review_service.audit(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=result, msg=f"已{body.audit_status}")


@router.post("/batch-audit", summary="一键批量审核（当前所有待审核记录）")
def batch_audit(
    body: ReviewBatchAuditIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """把当前待审核记录一次性全部通过/驳回；单条失败不影响其它条"""
    _check_owner(current_user)
    result = review_service.batch_audit(
        db, current_user.farm_id, body.business_type,
        body.audit_status, body.remark, current_user.id,
    )
    if result["success"] == 0 and result["failed"] == 0:
        return Result.ok(data=result, msg="当前没有待审核记录")
    msg = f"已批量{body.audit_status} {result['success']} 条"
    if result["failed"]:
        msg += f"，{result['failed']} 条失败"
    return Result.ok(data=result, msg=msg)
