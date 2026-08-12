"""
养殖场路由
"""
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user, resolve_farm_id
from app.models.user import User
from app.schemas.farm import FarmUpdateIn, FarmOut, FarmListOut
from app.schemas.auth import EmployeeRegisterIn
from app.schemas.user import UserOut
from app.services import farm_service, auth_service

router = APIRouter()


@router.get("/list", summary="养殖场列表（超管专用）")
def list_farms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.user_type != 1:
        return Result.fail(msg="无权限", code=40301)
    farms = farm_service.list_all_farms(db)
    return Result.ok(data=[FarmListOut.model_validate(f) for f in farms])


@router.get("/info", summary="获取养殖场信息")
def get_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    farm = farm_service.get_farm_info(db, farm_id)
    return Result.ok(data=FarmOut.model_validate(farm))


@router.put("/update", summary="更新养殖场信息")
def update_farm(
    body: FarmUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    # 超管和养殖场主都能更新
    if current_user.user_type not in (1, 2):
        return Result.fail(msg="无权限操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    farm = farm_service.update_farm(db, farm_id, body)
    return Result.ok(data=FarmOut.model_validate(farm), msg="更新成功")


@router.get("/employees", summary="员工列表")
def list_employees(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    farm_id = resolve_farm_id(current_user, x_farm_id)
    result = farm_service.list_employees(db, farm_id, pageNum, pageSize)
    result["list"] = [UserOut.model_validate(u) for u in result["list"]]
    return Result.ok(data=result)


@router.post("/employees", summary="添加员工")
def add_employee(
    body: EmployeeRegisterIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    """场主或超管给当前养殖场添加员工"""
    if current_user.user_type not in (1, 2):
        return Result.fail(msg="无权限操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    # 使用目标养殖场 ID 而非 body 中的 farm_id
    result = auth_service.register_employee(db, farm_id, body)
    return Result.ok(data=result, msg="添加员工成功")


@router.put("/employees/{employee_id}", summary="编辑员工")
def update_employee(
    employee_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    if current_user.user_type not in (1, 2):
        return Result.fail(msg="无权限操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    farm_service.update_employee(db, farm_id, employee_id, body)
    return Result.ok(msg="更新成功")


@router.delete("/employees/{employee_id}", summary="删除员工")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_farm_id: int | None = Header(None, alias="X-Farm-Id"),
):
    if current_user.user_type not in (1, 2):
        return Result.fail(msg="无权限操作", code=40301)
    farm_id = resolve_farm_id(current_user, x_farm_id)
    farm_service.delete_employee(db, farm_id, employee_id)
    return Result.ok(msg="删除成功")
