"""
系统管理 DTO：字典 + 用户/角色/菜单 + 日志 + 通知
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ========== 字典类型 ==========
class DictTypeOut(BaseModel):
    id: int
    dict_name: str
    dict_type: str
    status: int
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictTypeIn(BaseModel):
    dict_name: str = Field(..., description="字典名称")
    dict_type: str = Field(..., description="字典类型（唯一标识）")
    status: int = Field(1, description="状态：1正常 0停用")
    remark: Optional[str] = None


class DictTypeUpdateIn(BaseModel):
    dict_name: Optional[str] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class DictTypeQuery(BaseModel):
    dict_name: Optional[str] = None
    dict_type: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 20


# ========== 字典数据 ==========
class DictDataOut(BaseModel):
    id: int
    dict_type: str
    dict_label: str
    dict_value: str
    dict_sort: int
    dict_extra: Optional[str] = None
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictDataIn(BaseModel):
    dict_type: str = Field(..., description="字典类型")
    dict_label: str = Field(..., description="字典标签")
    dict_value: str = Field(..., description="字典键值")
    dict_sort: int = Field(0, description="排序")
    dict_extra: Optional[str] = Field(None, description="扩展信息 JSON")
    status: int = Field(1, description="状态：1正常 0停用")


class DictDataUpdateIn(BaseModel):
    dict_label: Optional[str] = None
    dict_value: Optional[str] = None
    dict_sort: Optional[int] = None
    dict_extra: Optional[str] = None
    status: Optional[int] = None


class DictDataQuery(BaseModel):
    dict_type: Optional[str] = None
    dict_label: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 50


# ========== 用户管理 ==========
class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    phone: str
    user_type: int
    farm_id: Optional[int] = None
    farm_name: Optional[str] = None
    post: Optional[str] = None
    status: int
    role_names: List[str] = []
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserIn(BaseModel):
    username: str = Field(..., description="登录账号")
    password: str = Field(..., min_length=6, description="密码（至少6位）")
    real_name: str = Field(..., description="真实姓名")
    phone: str = Field(..., description="手机号")
    user_type: int = Field(3, description="用户类型：1超管 2场主 3员工")
    farm_id: Optional[int] = Field(None, description="所属养殖场ID")
    post: Optional[str] = Field(None, description="员工岗位")
    status: int = Field(1, description="状态：1启用 0禁用")
    role_ids: List[int] = []


class UserUpdateIn(BaseModel):
    password: Optional[str] = Field(None, min_length=6, description="密码（留空不修改）")
    real_name: Optional[str] = None
    phone: Optional[str] = None
    user_type: Optional[int] = None
    farm_id: Optional[int] = None
    post: Optional[str] = None
    status: Optional[int] = None
    role_ids: Optional[List[int]] = None


class ResetPwdIn(BaseModel):
    new_password: str = Field(..., min_length=6, description="新密码（至少6位）")


class AssignRolesIn(BaseModel):
    role_ids: List[int] = Field(..., description="角色ID列表")


class UserQuery(BaseModel):
    username: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    user_type: Optional[int] = None
    farm_id: Optional[int] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 10


# ========== 角色 ==========
class RoleOut(BaseModel):
    id: int
    role_name: str
    role_key: str
    sort: int
    status: int
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleIn(BaseModel):
    role_name: str = Field(..., description="角色名称")
    role_key: str = Field(..., description="角色权限字符串")
    sort: int = Field(0, description="显示顺序")
    status: int = Field(1, description="状态：1正常 0停用")
    remark: Optional[str] = None


class RoleUpdateIn(BaseModel):
    role_name: Optional[str] = None
    role_key: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class RoleQuery(BaseModel):
    role_name: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 20


# ========== 菜单 ==========
class MenuOut(BaseModel):
    id: int
    parent_id: int
    menu_name: str
    menu_type: str
    path: Optional[str] = None
    component: Optional[str] = None
    perms: Optional[str] = None
    icon: Optional[str] = None
    sort: int
    visible: int
    status: int
    children: List["MenuOut"] = []

    class Config:
        from_attributes = True


class MenuIn(BaseModel):
    parent_id: int = Field(0, description="父菜单ID（0为顶级）")
    menu_name: str = Field(..., description="菜单名称")
    menu_type: str = Field("C", description="类型：M目录 C菜单 F按钮")
    path: Optional[str] = None
    component: Optional[str] = None
    perms: Optional[str] = None
    icon: Optional[str] = None
    sort: int = Field(0, description="显示顺序")
    visible: int = Field(1, description="显示状态：1显示 0隐藏")
    status: int = Field(1, description="状态：1正常 0停用")


class MenuUpdateIn(BaseModel):
    parent_id: Optional[int] = None
    menu_name: Optional[str] = None
    menu_type: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    perms: Optional[str] = None
    icon: Optional[str] = None
    sort: Optional[int] = None
    visible: Optional[int] = None
    status: Optional[int] = None


class MenuQuery(BaseModel):
    menu_name: Optional[str] = None
    status: Optional[int] = None


# ========== 操作日志 / 登录日志 ==========
class OperLogOut(BaseModel):
    id: int
    title: Optional[str] = None
    business_type: Optional[str] = None
    method: str
    oper_url: Optional[str] = None
    oper_user_id: Optional[int] = None
    oper_name: Optional[str] = None
    oper_ip: Optional[str] = None
    status: int
    error_msg: Optional[str] = None
    oper_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginLogOut(BaseModel):
    id: int
    username: str
    user_id: Optional[int] = None
    ip: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    status: int
    msg: Optional[str] = None
    login_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class LogQuery(BaseModel):
    username: Optional[str] = None
    status: Optional[int] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    pageNum: int = 1
    pageSize: int = 10


# ========== 通知公告 ==========
class NoticeOut(BaseModel):
    id: int
    farm_id: Optional[int] = None
    notice_title: str
    notice_type: str
    notice_content: Optional[str] = None
    status: int
    create_by: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoticeIn(BaseModel):
    notice_title: str = Field(..., description="公告标题")
    notice_type: str = Field("公告", description="类型：公告/通知")
    notice_content: Optional[str] = None
    status: int = Field(1, description="状态：1发布 0停用")


class NoticeUpdateIn(BaseModel):
    notice_title: Optional[str] = None
    notice_type: Optional[str] = None
    notice_content: Optional[str] = None
    status: Optional[int] = None


class NoticeQuery(BaseModel):
    notice_title: Optional[str] = None
    notice_type: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 10
