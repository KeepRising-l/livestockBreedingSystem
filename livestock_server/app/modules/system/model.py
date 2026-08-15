"""
系统管理模型：字典 + 用户/角色/菜单 + 日志 + 通知
"""
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime

from app.models.base import BasePO


class DictType(BasePO):
    """字典类型表"""
    __tablename__ = "sys_dict_type"

    dict_name = Column(String(50), nullable=False, comment="字典名称")
    dict_type = Column(String(50), nullable=False, unique=True, index=True, comment="字典类型（唯一标识）")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0停用")
    remark = Column(String(255), nullable=True, comment="备注")


class DictData(BasePO):
    """字典数据表"""
    __tablename__ = "sys_dict_data"

    dict_type = Column(String(50), nullable=False, index=True, comment="字典类型")
    dict_label = Column(String(50), nullable=False, comment="字典标签")
    dict_value = Column(String(50), nullable=False, comment="字典键值")
    dict_sort = Column(Integer, nullable=False, default=0, comment="排序")
    dict_extra = Column(Text, nullable=True, comment="扩展信息（JSON，如品种对应的畜种）")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0停用")


class SysRole(BasePO):
    """角色表（RBAC，P3-4 用）"""
    __tablename__ = "sys_role"

    role_name = Column(String(50), nullable=False, comment="角色名称")
    role_key = Column(String(50), nullable=False, unique=True, comment="角色权限字符串（如 admin/owner/feeder）")
    sort = Column(Integer, nullable=False, default=0, comment="显示顺序")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0停用")
    perms = Column(Text, nullable=True, comment="权限模块列表（JSON 数组，如 [\"feeding\",\"health\"]）")
    remark = Column(String(255), nullable=True, comment="备注")


class SysMenu(BasePO):
    """菜单表（RBAC 菜单/权限，P3-4 用）"""
    __tablename__ = "sys_menu"

    parent_id = Column(Integer, nullable=False, default=0, index=True, comment="父菜单ID（0为顶级）")
    menu_name = Column(String(50), nullable=False, comment="菜单名称")
    menu_type = Column(String(10), nullable=False, default="C", comment="类型：M目录 C菜单 F按钮")
    path = Column(String(100), nullable=True, comment="路由地址")
    component = Column(String(100), nullable=True, comment="组件路径")
    perms = Column(String(100), nullable=True, comment="权限标识（如 system:user:add）")
    icon = Column(String(50), nullable=True, comment="图标")
    sort = Column(Integer, nullable=False, default=0, comment="显示顺序")
    visible = Column(Integer, nullable=False, default=1, comment="显示状态：1显示 0隐藏")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0停用")


class SysUserRole(BasePO):
    """用户-角色关联表（RBAC）"""
    __tablename__ = "sys_user_role"

    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    role_id = Column(Integer, nullable=False, index=True, comment="角色ID")


class OperLog(BasePO):
    """操作日志表"""
    __tablename__ = "oper_log"

    title = Column(String(100), nullable=True, comment="模块标题（如 系统管理）")
    business_type = Column(String(20), nullable=True, comment="业务类型：add/update/delete/other")
    method = Column(String(10), nullable=False, comment="请求方式：POST/PUT/DELETE")
    oper_url = Column(String(200), nullable=True, comment="请求路径")
    oper_user_id = Column(Integer, nullable=True, comment="操作用户ID")
    oper_name = Column(String(50), nullable=True, comment="操作用户名")
    oper_ip = Column(String(50), nullable=True, comment="操作IP")
    status = Column(Integer, nullable=False, default=1, comment="状态：1成功 0失败")
    error_msg = Column(String(500), nullable=True, comment="错误信息")
    oper_time = Column(DateTime, nullable=False, comment="操作时间")


class LoginLog(BasePO):
    """登录日志表"""
    __tablename__ = "login_log"

    username = Column(String(50), nullable=False, comment="登录账号")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    ip = Column(String(50), nullable=True, comment="登录IP")
    browser = Column(String(50), nullable=True, comment="浏览器")
    os = Column(String(50), nullable=True, comment="操作系统")
    status = Column(Integer, nullable=False, default=1, comment="状态：1成功 0失败")
    msg = Column(String(200), nullable=True, comment="提示消息")
    login_time = Column(DateTime, nullable=False, comment="登录时间")


class SysNotice(BasePO):
    """通知公告表"""
    __tablename__ = "sys_notice"

    notice_title = Column(String(100), nullable=False, comment="公告标题")
    notice_type = Column(String(10), nullable=False, default="公告", comment="类型：公告/通知")
    notice_content = Column(Text, nullable=True, comment="公告内容")
    status = Column(Integer, nullable=False, default=1, comment="状态：1发布 0停用")
    create_by = Column(String(50), nullable=True, comment="创建人")


class SysMessage(BasePO):
    """站内消息表（缺口6：审核结果通知闭环，员工提交→审核通过/驳回→通知提交人）"""
    __tablename__ = "sys_message"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    receiver_user_id = Column(Integer, nullable=False, index=True, comment="接收人用户ID")
    message_type = Column(String(20), nullable=False, default="审核结果", comment="消息类型：审核结果/系统提醒")
    title = Column(String(100), nullable=False, comment="消息标题")
    content = Column(String(500), nullable=True, comment="消息内容")
    related_module = Column(String(20), nullable=True, comment="关联业务模块：feeding/purchase/consume/vaccine/medical")
    related_id = Column(Integer, nullable=True, comment="关联业务记录ID")
    is_read = Column(Integer, nullable=False, default=0, comment="是否已读：0未读 1已读")
    read_time = Column(DateTime, nullable=True, comment="已读时间")
