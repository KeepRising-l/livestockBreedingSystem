"""
系统管理 API：字典 + 用户/角色/菜单 + 日志 + 通知

- 字典数据查询接口（/dict/data/query/{dict_type}）对所有登录用户开放
- 字典类型/数据的增删改接口仅超管可操作
- 用户管理（/user）仅超管可操作（场主管理本场员工走 /farm/employees）
- 角色/菜单/日志/通知管理仅超管可操作
- 已发布公告（/notice/published）对所有登录用户开放
"""
from datetime import datetime

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
    UserOut, UserIn, UserUpdateIn, ResetPwdIn, AssignRolesIn, UserQuery,
    RoleOut, RoleIn, RoleUpdateIn, RoleQuery,
    MenuOut, MenuIn, MenuUpdateIn, MenuQuery,
    OperLogOut, LoginLogOut, LogQuery,
    NoticeOut, NoticeIn, NoticeUpdateIn, NoticeQuery,
)
from app.modules.system import service as system_service

router = APIRouter()


def _require_admin(user: User) -> None:
    """仅超管可操作"""
    if user.user_type != 1:
        raise BizException("仅超级管理员可操作系统管理", code=40301)


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


# ========== 用户管理（仅超管） ==========
@router.get("/user/list", summary="用户列表（超管）")
def list_users(
    username: str = Query(None),
    real_name: str = Query(None),
    phone: str = Query(None),
    user_type: int = Query(None),
    farm_id: int = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    q = UserQuery(username=username, real_name=real_name, phone=phone,
                  user_type=user_type, farm_id=farm_id, status=status,
                  pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_users(db, q)
    result["list"] = [UserOut.model_validate(u) for u in result["list"]]
    return Result.ok(data=result)


@router.post("/user/add", summary="新增用户（超管）")
def add_user(body: UserIn, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    u = system_service.add_user(db, body)
    return Result.ok(data=UserOut.model_validate(u), msg="添加用户成功")


@router.put("/user/update/{user_id}", summary="编辑用户（超管）")
def update_user(user_id: int, body: UserUpdateIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    u = system_service.update_user(db, user_id, body)
    return Result.ok(data=UserOut.model_validate(u), msg="修改成功")


@router.delete("/user/{user_id}", summary="删除用户（超管）")
def delete_user(user_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.delete_user(db, user_id)
    return Result.ok(msg="删除成功")


@router.post("/user/reset-password/{user_id}", summary="重置用户密码（超管）")
def reset_password(user_id: int, body: ResetPwdIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.reset_password(db, user_id, body.new_password)
    return Result.ok(msg="密码已重置")


@router.post("/user/assign-roles/{user_id}", summary="分配用户角色（超管）")
def assign_roles(user_id: int, body: AssignRolesIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.assign_roles(db, user_id, body.role_ids)
    return Result.ok(msg="角色分配成功")


@router.get("/user/roles/{user_id}", summary="查询用户已有角色ID（超管）")
def list_user_roles(user_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    role_ids = system_service.list_user_role_ids(db, user_id)
    return Result.ok(data={"role_ids": role_ids})


# ========== 角色管理（仅超管） ==========
@router.get("/role/list", summary="角色列表（超管）")
def list_roles(
    role_name: str = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    q = RoleQuery(role_name=role_name, status=status, pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_roles(db, q)
    result["list"] = [RoleOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.post("/role/add", summary="新增角色（超管）")
def add_role(body: RoleIn, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    r = system_service.add_role(db, body)
    return Result.ok(data=RoleOut.model_validate(r), msg="添加成功")


@router.put("/role/update/{role_id}", summary="编辑角色（超管）")
def update_role(role_id: int, body: RoleUpdateIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    r = system_service.update_role(db, role_id, body)
    return Result.ok(data=RoleOut.model_validate(r), msg="修改成功")


@router.delete("/role/{role_id}", summary="删除角色（超管）")
def delete_role(role_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.delete_role(db, role_id)
    return Result.ok(msg="删除成功")


# ========== 菜单管理（仅超管，RBAC P3-4 用） ==========
@router.get("/menu/list", summary="菜单树（超管）")
def list_menus(
    menu_name: str = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    q = MenuQuery(menu_name=menu_name, status=status)
    return Result.ok(data=system_service.list_menus(db, q))


@router.post("/menu/add", summary="新增菜单（超管）")
def add_menu(body: MenuIn, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    m = system_service.add_menu(db, body)
    return Result.ok(data=MenuOut.model_validate(m), msg="添加成功")


@router.put("/menu/update/{menu_id}", summary="编辑菜单（超管）")
def update_menu(menu_id: int, body: MenuUpdateIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    m = system_service.update_menu(db, menu_id, body)
    return Result.ok(data=MenuOut.model_validate(m), msg="修改成功")


@router.delete("/menu/{menu_id}", summary="删除菜单（超管）")
def delete_menu(menu_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.delete_menu(db, menu_id)
    return Result.ok(msg="删除成功")


# ========== 登录日志 / 操作日志（仅超管） ==========
@router.get("/log/login/list", summary="登录日志列表（超管）")
def list_login_log(
    username: str = Query(None),
    status: int = Query(None),
    date_start: datetime = Query(None),
    date_end: datetime = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    q = LogQuery(username=username, status=status, date_start=date_start,
                 date_end=date_end, pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_login_log(db, q)
    result["list"] = [LoginLogOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.delete("/log/login/clear", summary="清空登录日志（超管）")
def clear_login_log(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.clear_login_log(db)
    return Result.ok(msg="登录日志已清空")


@router.get("/log/oper/list", summary="操作日志列表（超管）")
def list_oper_log(
    username: str = Query(None),
    status: int = Query(None),
    date_start: datetime = Query(None),
    date_end: datetime = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    q = LogQuery(username=username, status=status, date_start=date_start,
                 date_end=date_end, pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_oper_log(db, q)
    result["list"] = [OperLogOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.delete("/log/oper/clear", summary="清空操作日志（超管）")
def clear_oper_log(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.clear_oper_log(db)
    return Result.ok(msg="操作日志已清空")


# ========== 通知公告 ==========
@router.get("/notice/list", summary="公告列表（超管）")
def list_notices(
    notice_title: str = Query(None),
    notice_type: str = Query(None),
    status: int = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    q = NoticeQuery(notice_title=notice_title, notice_type=notice_type,
                    status=status, pageNum=pageNum, pageSize=pageSize)
    result = system_service.list_notices(db, q, current_user.farm_id)
    result["list"] = [NoticeOut.model_validate(n) for n in result["list"]]
    return Result.ok(data=result)


@router.get("/notice/published", summary="已发布公告（所有登录用户，按当前养殖场隔离）")
def list_published_notices(db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    items = system_service.list_published_notices(db, current_user.farm_id)
    return Result.ok(data=[NoticeOut.model_validate(n) for n in items])


@router.get("/notice/{notice_id}", summary="公告详情（超管）")
def get_notice(notice_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    n = system_service.get_notice(db, notice_id, current_user.farm_id)
    return Result.ok(data=NoticeOut.model_validate(n))


@router.post("/notice/add", summary="新增公告（超管）")
def add_notice(body: NoticeIn, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    n = system_service.add_notice(db, body, current_user.username, current_user.farm_id)
    return Result.ok(data=NoticeOut.model_validate(n), msg="发布成功")


@router.put("/notice/update/{notice_id}", summary="编辑公告（超管）")
def update_notice(notice_id: int, body: NoticeUpdateIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    n = system_service.update_notice(db, notice_id, body, current_user.farm_id)
    return Result.ok(data=NoticeOut.model_validate(n), msg="修改成功")


@router.delete("/notice/{notice_id}", summary="删除公告（超管）")
def delete_notice(notice_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    system_service.delete_notice(db, notice_id, current_user.farm_id)
    return Result.ok(msg="删除成功")


# ========== 站内消息（缺口6：审核结果通知，所有登录用户查自己的） ==========

@router.get("/message/list", summary="我的站内消息（分页）")
def list_messages(
    is_read: int = Query(None, description="已读筛选：0未读 1已读"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = system_service.list_messages(db, current_user.id, is_read, pageNum, pageSize)
    items = [
        {
            "id": m.id, "farm_id": m.farm_id, "receiver_user_id": m.receiver_user_id,
            "message_type": m.message_type, "title": m.title, "content": m.content,
            "related_module": m.related_module, "related_id": m.related_id,
            "is_read": m.is_read, "read_time": m.read_time, "create_time": m.create_time,
        } for m in result["list"]
    ]
    result["list"] = items
    return Result.ok(data=result)


@router.get("/message/unread-count", summary="未读消息数（顶栏角标）")
def unread_message_count(db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    count = system_service.unread_message_count(db, current_user.id)
    return Result.ok(data={"count": count})


@router.put("/message/read/{message_id}", summary="标记单条消息已读")
def mark_message_read(message_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    msg = system_service.mark_message_read(db, current_user.id, message_id)
    return Result.ok(msg="已标记已读")


@router.put("/message/read-all", summary="全部标记已读")
def mark_all_messages_read(db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    count = system_service.mark_all_messages_read(db, current_user.id)
    return Result.ok(data={"count": count}, msg=f"已标记 {count} 条消息为已读")
