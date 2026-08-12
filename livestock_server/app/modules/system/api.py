"""
系统管理 API：字典类型 + 字典数据

- 字典数据查询接口（/dict/data/query/{dict_type}）对所有登录用户开放
- 字典类型/数据的增删改接口仅超管可操作
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import BizException
from app.core.response import Result
from app.database import get_db
from app.models.user import User
from app.modules.system.schema import (
    DictTypeOut, DictTypeIn, DictTypeUpdateIn, DictTypeQuery,
    DictDataOut, DictDataIn, DictDataUpdateIn, DictDataQuery,
)
from app.modules.system import service as system_service

router = APIRouter()


def _require_admin(user: User) -> None:
    """仅超管可操作"""
    if user.user_type != 1:
        raise BizException("仅超级管理员可操作系统字典", code=40301)


# ========== 字典类型 ==========
@router.get("/dict/type/list", summary="字典类型列表")
def list_dict_type(
    dict_name: str = Query(None),
    dict_type: str = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = DictTypeQuery(dict_name=dict_name, dict_type=dict_type, status=status,
                     pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_dict_type(db, q)
    result["list"] = [DictTypeOut.model_validate(t) for t in result["list"]]
    return Result.ok(data=result)


@router.post("/dict/type/add", summary="新增字典类型（超管）")
def add_dict_type(
    body: DictTypeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    t = system_service.add_dict_type(db, body)
    return Result.ok(data=DictTypeOut.model_validate(t), msg="添加成功")


@router.put("/dict/type/update/{type_id}", summary="修改字典类型（超管）")
def update_dict_type(
    type_id: int,
    body: DictTypeUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    t = system_service.update_dict_type(db, type_id, body)
    return Result.ok(data=DictTypeOut.model_validate(t), msg="修改成功")


@router.delete("/dict/type/{type_id}", summary="删除字典类型（超管）")
def delete_dict_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    system_service.delete_dict_type(db, type_id)
    return Result.ok(msg="删除成功")


# ========== 字典数据 ==========
@router.get("/dict/data/list", summary="字典数据列表")
def list_dict_data(
    dict_type: str = Query(None),
    dict_label: str = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = DictDataQuery(dict_type=dict_type, dict_label=dict_label, status=status,
                     pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_dict_data(db, q)
    result["list"] = [DictDataOut.model_validate(d) for d in result["list"]]
    return Result.ok(data=result)


@router.get("/dict/data/query/{dict_type}", summary="根据 dict_type 查启用字典数据（下拉框用）")
def query_dict_data_by_type(
    dict_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = system_service.get_dict_data_by_type(db, dict_type)
    return Result.ok(data=[DictDataOut.model_validate(d) for d in items])


@router.post("/dict/data/add", summary="新增字典数据（超管）")
def add_dict_data(
    body: DictDataIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    d = system_service.add_dict_data(db, body)
    return Result.ok(data=DictDataOut.model_validate(d), msg="添加成功")


@router.put("/dict/data/update/{data_id}", summary="修改字典数据（超管）")
def update_dict_data(
    data_id: int,
    body: DictDataUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    d = system_service.update_dict_data(db, data_id, body)
    return Result.ok(data=DictDataOut.model_validate(d), msg="修改成功")


@router.delete("/dict/data/{data_id}", summary="删除字典数据（超管）")
def delete_dict_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    system_service.delete_dict_data(db, data_id)
    return Result.ok(msg="删除成功")
