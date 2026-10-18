"""
饲喂路由

- 方案 CRUD：场主权限（user_type=2 才能增删改）
- 记录 CRUD：员工可提交（user_type=3），审核只能场主
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.perms import require_perms
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.feeding.schema import (
    FeedingPlanIn, FeedingPlanUpdateIn, FeedingPlanOut, FeedingPlanQuery,
    FeedingRecordIn, FeedingRecordBatchIn, FeedingRecordUpdateIn, FeedingRecordOut, FeedingRecordQuery,
    AuditActionIn,
)
from app.modules.feeding import service as feeding_service

router = APIRouter(dependencies=[Depends(require_perms("feeding"))])


def _check_owner(current_user: User):
    """养殖场主或超管能操作（user_type=1 或 2）"""
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)


# ============================================================
# 饲喂方案
# ============================================================

@router.get("/plan/list", summary="饲喂方案列表")
def list_plans(
    species: str = Query(None, description="畜种 cattle/sheep/pig"),
    applicable_stage: str = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = FeedingPlanQuery(
        species=species, applicable_stage=applicable_stage, status=status,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = feeding_service.list_plans(db, current_user.farm_id, query)
    result["list"] = [FeedingPlanOut.model_validate(p) for p in result["list"]]
    return Result.ok(data=result)


@router.get("/plan/{plan_id}", summary="饲喂方案详情")
def get_plan(plan_id: int, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    plan = feeding_service.get_plan(db, current_user.farm_id, plan_id)
    return Result.ok(data=FeedingPlanOut.model_validate(plan))


@router.post("/plan/add", summary="新增饲喂方案")
def add_plan(body: FeedingPlanIn, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    plan = feeding_service.add_plan(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=FeedingPlanOut.model_validate(plan), msg="添加成功")


@router.put("/plan/update/{plan_id}", summary="修改饲喂方案")
def update_plan(plan_id: int, body: FeedingPlanUpdateIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    plan = feeding_service.update_plan(db, current_user.farm_id, plan_id, body)
    return Result.ok(data=FeedingPlanOut.model_validate(plan), msg="修改成功")


@router.delete("/plan/{plan_id}", summary="删除饲喂方案")
def delete_plan(plan_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    feeding_service.delete_plan(db, current_user.farm_id, plan_id)
    return Result.ok(msg="删除成功")


# ============================================================
# 饲喂记录
# ============================================================

@router.get("/record/list", summary="饲喂记录列表")
def list_records(
    species: str = Query(None, description="畜种：牛/羊/猪"),
    feed_date_start: date = Query(None),
    feed_date_end: date = Query(None),
    pen_id: int = Query(None),
    time_period: str = Query(None, description="时段：早/晚"),
    audit_status: str = Query(None, description="审核状态：待审核/通过/驳回"),
    status: str = Query(None, description="投喂状态：未投喂/已投喂/已跳过"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = FeedingRecordQuery(
        species=species,
        feed_date_start=feed_date_start, feed_date_end=feed_date_end,
        pen_id=pen_id, time_period=time_period,
        audit_status=audit_status, status=status,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = feeding_service.list_records(db, current_user.farm_id, query)
    result["list"] = [FeedingRecordOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/record/{record_id}", summary="饲喂记录详情")
def get_record(record_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    rec = feeding_service.get_record(db, current_user.farm_id, record_id)
    return Result.ok(data=FeedingRecordOut.model_validate(rec))


@router.post("/record/add", summary="提交饲喂记录（员工提交，进入待审核）")
def add_record(body: FeedingRecordIn, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    rec = feeding_service.add_record(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=FeedingRecordOut.model_validate(rec), msg="提交成功，等待审核")


@router.post("/record/batch-add", summary="批量提交饲喂记录（多个圈舍一次生成多条，进入待审核）")
def add_records_batch(body: FeedingRecordBatchIn, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    data = feeding_service.add_records_batch(db, current_user.farm_id, body, current_user.id)
    msg = f"提交成功 {data['created']} 条，等待审核"
    if data["skipped"]:
        msg += f"；{len(data['skipped'])} 个圈舍已跳过"
    return Result.ok(data=data, msg=msg)


@router.put("/record/update/{record_id}", summary="修改饲喂记录（仅待审核状态可改）")
def update_record(record_id: int, body: FeedingRecordUpdateIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    rec = feeding_service.update_record(db, current_user.farm_id, record_id, body)
    return Result.ok(data=FeedingRecordOut.model_validate(rec), msg="修改成功")


@router.delete("/record/{record_id}", summary="删除饲喂记录（已通过不能删）")
def delete_record(record_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    feeding_service.delete_record(db, current_user.farm_id, record_id)
    return Result.ok(msg="删除成功")


@router.post("/record/audit/{record_id}", summary="审核饲喂记录（场主权限）")
def audit_record(record_id: int, body: AuditActionIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    rec = feeding_service.audit_record(db, current_user.farm_id, record_id, body)
    return Result.ok(data=FeedingRecordOut.model_validate(rec), msg=f"已{body.audit_status}")
