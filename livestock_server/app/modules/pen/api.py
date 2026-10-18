"""
圈舍路由
"""
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user, resolve_farm_id
from app.core.perms import require_perms
from app.core.utils import get_effective_farm_id
from app.models.user import User
from app.modules.pen.model import Pen
from app.modules.pen.schema import (
    PenAddIn, PenBatchAddIn, PenBatchAddOut, PenUpdateIn, PenOut,
)
from app.modules.pen import service as pen_service

router = APIRouter(dependencies=[Depends(require_perms("pen"))])


@router.get("/list", summary="圈舍列表")
def list_pens(
    pen_type: str = Query(None, description="圈舍类型 A/B/C/D"),
    species: str = Query(None, description="畜种：牛/羊/猪（只返回养该畜种的圈舍）"),
    status: int = Query(None, description="状态：1正常 0空闲"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    result = pen_service.list_pens(
        db, farm_id, pen_type, species, status, pageNum, pageSize
    )
    result["list"] = [PenOut.model_validate(p) for p in result["list"]]
    return Result.ok(data=result)


@router.get("/{pen_id}", summary="圈舍详情")
def get_pen(
    pen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    pen = pen_service.get_pen(db, farm_id, pen_id)
    return Result.ok(data=PenOut.model_validate(pen))


@router.post("/add", summary="新增圈舍")
def add_pen(
    body: PenAddIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    if current_user.user_type == 3:
        return Result.fail(msg="员工无权操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    pen = pen_service.add_pen(db, farm_id, body)
    return Result.ok(data=PenOut.model_validate(pen), msg="添加成功")


@router.post("/batch-add", summary="批量新增圈舍")
def batch_add_pens(
    body: PenBatchAddIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    """一次创建多个圈舍：成功部分落库，重复/不合法的编号跳过并返回原因"""
    if current_user.user_type == 3:
        return Result.fail(msg="员工无权操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    data = pen_service.batch_add_pens(db, farm_id, body)
    result = PenBatchAddOut(**data)
    skipped = len(result.skipped)
    msg = f"成功添加 {result.created} 个圈舍"
    if skipped:
        msg += f"，跳过 {skipped} 个"
    return Result.ok(data=result.model_dump(), msg=msg)


@router.put("/update/{pen_id}", summary="修改圈舍")
def update_pen(
    pen_id: int,
    body: PenUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    if current_user.user_type == 3:
        return Result.fail(msg="员工无权操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    pen = pen_service.update_pen(db, farm_id, pen_id, body)
    return Result.ok(data=PenOut.model_validate(pen), msg="修改成功")


@router.delete("/{pen_id}", summary="删除圈舍")
def delete_pen(
    pen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    if current_user.user_type == 3:
        return Result.fail(msg="员工无权操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    pen_service.delete_pen(db, farm_id, pen_id)
    return Result.ok(msg="删除成功")


@router.get("/{pen_id}/animals", summary="查看圈舍内畜禽")
def list_pen_animals(
    pen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    """查看某个圈舍内所有畜禽档案"""
    from app.modules.animal.model import Animal
    farm_id = resolve_farm_id(current_user, x_farm_id)
    fid = get_effective_farm_id(db, farm_id)
    pen = pen_service.get_pen(db, farm_id, pen_id)
    animals = db.query(Animal).filter(
        Animal.pen_id == pen_id,
        Animal.farm_id == fid,
        Animal.deleted == False,
        Animal.status.in_(["在栏", "种用", "隔离", "待出栏"]),
    ).order_by(Animal.ear_tag).all()
    from app.modules.animal.schema import AnimalOut
    return Result.ok(data=[AnimalOut.model_validate(a) for a in animals])
