"""
档案路由
"""
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user, resolve_farm_id
from app.core.perms import require_perms
from app.models.user import User
from app.modules.animal.schema import (
    AnimalIndividualIn, AnimalBatchIn, AnimalQuery, AnimalOut, BatchDeleteIn,
    AnimalHistoryOut, AnimalHistoryQuery, AnimalUpdateIn,
)
from app.modules.animal import service as animal_service

router = APIRouter(dependencies=[Depends(require_perms("animal"))])


@router.get("/history/list", summary="档案历史记录列表（已删除档案）")
def list_history(
    ear_tag: str = Query(None),
    species: str = Query(None),
    breed: str = Query(None),
    gender: str = Query(None),
    status: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    query = AnimalHistoryQuery(
        ear_tag=ear_tag, species=species, breed=breed,
        gender=gender, status=status, pageNum=pageNum, pageSize=pageSize,
    )
    result = animal_service.list_history(db, farm_id, query)
    result["list"] = [AnimalHistoryOut.model_validate(h) for h in result["list"]]
    return Result.ok(data=result)


@router.post("/history/restore/{history_id}", summary="恢复已删除档案")
def restore_animal(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    a = animal_service.restore_animal(db, farm_id, history_id)
    return Result.ok(data=AnimalOut.model_validate(a), msg="恢复成功")


@router.get("/list", summary="档案列表（多条件筛选）")
def list_animals(
    ear_tag: str = Query(None),
    species: str = Query(None),
    pen_id: int = Query(None),
    breed: str = Query(None),
    gender: str = Query(None),
    status: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    query = AnimalQuery(
        ear_tag=ear_tag, species=species, pen_id=pen_id, breed=breed,
        gender=gender, status=status, pageNum=pageNum, pageSize=pageSize,
    )
    result = animal_service.list_animals(db, farm_id, query)
    result["list"] = [AnimalOut.model_validate(a) for a in result["list"]]
    return Result.ok(data=result)


@router.get("/{animal_id}", summary="档案详情")
def get_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    a = animal_service.get_animal(db, farm_id, animal_id)
    return Result.ok(data=AnimalOut.model_validate(a))


@router.put("/update/{animal_id}", summary="修改档案")
def update_animal(
    animal_id: int,
    body: AnimalUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    a = animal_service.update_animal(db, farm_id, animal_id, body)
    return Result.ok(data=AnimalOut.model_validate(a), msg="修改成功")


@router.post("/individual", summary="个体入栏")
def individual_create(
    body: AnimalIndividualIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    a = animal_service.individual_create(db, farm_id, body)
    return Result.ok(data=AnimalOut.model_validate(a), msg="入栏成功")


@router.post("/batch", summary="批量入栏")
def batch_create(
    body: AnimalBatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    result = animal_service.batch_create(db, farm_id, body)
    return Result.ok(data=result, msg="批量入栏成功")


@router.post("/batch/batch-delete", summary="批量删除")
def batch_delete(
    body: BatchDeleteIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    result = animal_service.batch_delete(db, farm_id, body.ids)
    return Result.ok(data=result, msg="删除成功")


@router.get("/ear-tag/generate", summary="预览耳标（指定圈舍）")
def preview_ear_tag(
    pen_id: int = Query(..., description="圈舍ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    """预览指定圈舍下一个可用的耳标号"""
    from app.modules.pen.service import get_pen
    from app.modules.animal.service import generate_ear_tag
    farm_id = resolve_farm_id(current_user, x_farm_id)
    pen = get_pen(db, farm_id, pen_id)
    ear_tag = generate_ear_tag(db, farm_id, pen)
    return Result.ok(data={"ear_tag": ear_tag, "pen_code": pen.pen_code})
