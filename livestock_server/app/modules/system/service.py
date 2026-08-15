"""
系统管理 service：字典 + 用户/角色/菜单 + 日志 + 通知 + RBAC
"""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.security import hash_password
from app.models.farm import Farm
from app.models.user import User
from app.modules.system.model import (
    DictType, DictData,
    SysRole, SysMenu, SysUserRole, OperLog, LoginLog, SysNotice, SysMessage,
)
from app.modules.system.schema import (
    DictTypeIn, DictTypeUpdateIn, DictTypeQuery,
    DictDataIn, DictDataUpdateIn, DictDataQuery,
    UserIn, UserUpdateIn, UserQuery,
    RoleIn, RoleUpdateIn, RoleQuery,
    MenuIn, MenuUpdateIn, MenuQuery,
    LogQuery,
    NoticeIn, NoticeUpdateIn, NoticeQuery,
)


# ========== 字典类型 CRUD ==========
def list_dict_type(db: Session, query: DictTypeQuery) -> dict:
    q = db.query(DictType).filter(DictType.deleted == False)
    if query.dict_name:
        q = q.filter(DictType.dict_name.like(f"%{query.dict_name}%"))
    if query.dict_type:
        q = q.filter(DictType.dict_type.like(f"%{query.dict_type}%"))
    if query.status is not None:
        q = q.filter(DictType.status == query.status)

    total = q.count()
    items = q.order_by(DictType.id).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def add_dict_type(db: Session, body: DictTypeIn) -> DictType:
    exists = db.query(DictType).filter(
        DictType.dict_type == body.dict_type, DictType.deleted == False
    ).first()
    if exists:
        raise BizException(f"字典类型 {body.dict_type} 已存在", code=40032)
    t = DictType(**body.model_dump())
    db.add(t)
    db.commit()
    return t


def update_dict_type(db: Session, type_id: int, body: DictTypeUpdateIn) -> DictType:
    t = db.query(DictType).filter(DictType.id == type_id, DictType.deleted == False).first()
    if not t:
        raise BizException("字典类型不存在", code=40033)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    return t


def delete_dict_type(db: Session, type_id: int) -> None:
    t = db.query(DictType).filter(DictType.id == type_id, DictType.deleted == False).first()
    if not t:
        raise BizException("字典类型不存在", code=40033)
    # 检查是否有关联字典数据
    cnt = db.query(DictData).filter(
        DictData.dict_type == t.dict_type, DictData.deleted == False
    ).count()
    if cnt > 0:
        raise BizException(f"该字典类型下有 {cnt} 条数据，无法删除", code=40034)
    t.deleted = True
    db.commit()


# ========== 字典数据 CRUD ==========
def list_dict_data(db: Session, query: DictDataQuery) -> dict:
    q = db.query(DictData).filter(DictData.deleted == False)
    if query.dict_type:
        q = q.filter(DictData.dict_type == query.dict_type)
    if query.dict_label:
        q = q.filter(DictData.dict_label.like(f"%{query.dict_label}%"))
    if query.status is not None:
        q = q.filter(DictData.status == query.status)

    total = q.count()
    items = q.order_by(DictData.dict_type, DictData.dict_sort).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_dict_data_by_type(db: Session, dict_type: str) -> list:
    """根据 dict_type 查询启用状态的字典数据（前端下拉框用）"""
    items = db.query(DictData).filter(
        DictData.dict_type == dict_type,
        DictData.deleted == False,
        DictData.status == 1,
    ).order_by(DictData.dict_sort).all()
    return items


def add_dict_data(db: Session, body: DictDataIn) -> DictData:
    # 校验字典类型存在
    t = db.query(DictType).filter(
        DictType.dict_type == body.dict_type, DictType.deleted == False
    ).first()
    if not t:
        raise BizException(f"字典类型 {body.dict_type} 不存在", code=40035)
    d = DictData(**body.model_dump())
    db.add(d)
    db.commit()
    return d


def update_dict_data(db: Session, data_id: int, body: DictDataUpdateIn) -> DictData:
    d = db.query(DictData).filter(DictData.id == data_id, DictData.deleted == False).first()
    if not d:
        raise BizException("字典数据不存在", code=40036)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(d, k, v)
    db.commit()
    return d


def delete_dict_data(db: Session, data_id: int) -> None:
    d = db.query(DictData).filter(DictData.id == data_id, DictData.deleted == False).first()
    if not d:
        raise BizException("字典数据不存在", code=40036)
    d.deleted = True
    db.commit()


# ========== 字典初始化 ==========
# 字典类型预置数据
DICT_TYPES = [
    ("用户类型", "sys_user_type", "用户类型枚举"),
    ("岗位", "sys_post", "员工岗位枚举"),
    ("养殖种类", "sys_species", "养殖种类枚举"),
    ("圈舍类型", "sys_pen_type", "圈舍类型枚举"),
    ("档案状态", "sys_animal_status", "畜禽档案状态"),
    ("审核状态", "sys_audit_status", "审核状态"),
    ("结算状态", "sys_settle_status", "销售结算状态"),
    ("配种方式", "sys_mating_type", "配种方式"),
    ("预警类型", "sys_alert_type", "繁育预警类型"),
    ("诊疗状态", "sys_treatment_status", "诊疗状态"),
    ("物资类型", "sys_material_type", "物资类型"),
    ("疫苗类型", "sys_vaccine_type", "疫苗类型"),
    ("品种", "sys_breed", "品种枚举（dict_extra 存畜种编码）"),
]

# 字典数据预置数据：(dict_type, dict_label, dict_value, dict_sort, dict_extra)
DICT_DATA = [
    # 用户类型
    ("sys_user_type", "超级管理员", "1", 1, None),
    ("sys_user_type", "养殖场主", "2", 2, None),
    ("sys_user_type", "员工", "3", 3, None),
    # 岗位
    ("sys_post", "饲喂员", "饲喂员", 1, None),
    ("sys_post", "兽医", "兽医", 2, None),
    ("sys_post", "繁育员", "繁育员", 3, None),
    ("sys_post", "库管员", "库管员", 4, None),
    # 养殖种类
    ("sys_species", "牛", "cattle", 1, None),
    ("sys_species", "羊", "sheep", 2, None),
    ("sys_species", "猪", "pig", 3, None),
    # 圈舍类型
    ("sys_pen_type", "育雏舍", "A", 1, None),
    ("sys_pen_type", "育成舍", "B", 2, None),
    ("sys_pen_type", "繁育舍", "C", 3, None),
    ("sys_pen_type", "种畜圈舍", "D", 4, None),
    # 档案状态
    ("sys_animal_status", "在栏", "在栏", 1, None),
    ("sys_animal_status", "种用", "种用", 2, None),
    ("sys_animal_status", "隔离", "隔离", 3, None),
    ("sys_animal_status", "待出栏", "待出栏", 4, None),
    ("sys_animal_status", "已出栏", "已出栏", 5, None),
    ("sys_animal_status", "死亡", "死亡", 6, None),
    # 审核状态
    ("sys_audit_status", "待审核", "待审核", 1, None),
    ("sys_audit_status", "通过", "通过", 2, None),
    ("sys_audit_status", "驳回", "驳回", 3, None),
    # 结算状态
    ("sys_settle_status", "未结算", "未结算", 1, None),
    ("sys_settle_status", "已结算", "已结算", 2, None),
    ("sys_settle_status", "部分结算", "部分结算", 3, None),
    # 配种方式
    ("sys_mating_type", "本交", "本交", 1, None),
    ("sys_mating_type", "人工受精", "人工受精", 2, None),
    # 预警类型
    ("sys_alert_type", "孕检", "孕检", 1, None),
    ("sys_alert_type", "临产", "临产", 2, None),
    ("sys_alert_type", "未发情", "未发情", 3, None),
    # 诊疗状态
    ("sys_treatment_status", "治疗中", "治疗中", 1, None),
    ("sys_treatment_status", "已康复", "已康复", 2, None),
    ("sys_treatment_status", "死亡", "死亡", 3, None),
    # 物资类型
    ("sys_material_type", "饲料", "饲料", 1, None),
    ("sys_material_type", "疫苗", "疫苗", 2, None),
    ("sys_material_type", "兽药", "兽药", 3, None),
    # 疫苗类型
    ("sys_vaccine_type", "口蹄疫", "foot_and_mouth", 1, '{"species":"cattle,sheep,pig"}'),
    ("sys_vaccine_type", "布病", "brucellosis", 2, '{"species":"cattle,sheep"}'),
    ("sys_vaccine_type", "小反刍兽疫", "ppr", 3, '{"species":"sheep"}'),
    ("sys_vaccine_type", "猪瘟", "swine_fever", 4, '{"species":"pig"}'),
    ("sys_vaccine_type", "蓝耳病", "prrs", 5, '{"species":"pig"}'),
    ("sys_vaccine_type", "伪狂犬", "pseudorabies", 6, '{"species":"pig,sheep"}'),
    ("sys_vaccine_type", "牛结节性皮肤病", "lsd", 7, '{"species":"cattle"}'),
    # 品种（权威清单，对齐功能描述.docx：牛=黄牛/西门塔尔牛/安格斯牛/秦川牛；羊=波尔山羊/黄淮山羊/小尾寒羊/山羊/绵羊；猪=大白猪/长白猪/杜长大三元猪/黑土猪）
    ("sys_breed", "黄牛", "黄牛", 1, '{"species":"cattle"}'),
    ("sys_breed", "西门塔尔牛", "西门塔尔牛", 2, '{"species":"cattle"}'),
    ("sys_breed", "安格斯牛", "安格斯牛", 3, '{"species":"cattle"}'),
    ("sys_breed", "秦川牛", "秦川牛", 4, '{"species":"cattle"}'),
    ("sys_breed", "波尔山羊", "波尔山羊", 5, '{"species":"sheep"}'),
    ("sys_breed", "黄淮山羊", "黄淮山羊", 6, '{"species":"sheep"}'),
    ("sys_breed", "小尾寒羊", "小尾寒羊", 7, '{"species":"sheep"}'),
    ("sys_breed", "山羊", "山羊", 8, '{"species":"sheep"}'),
    ("sys_breed", "绵羊", "绵羊", 9, '{"species":"sheep"}'),
    ("sys_breed", "大白猪", "大白猪", 10, '{"species":"pig"}'),
    ("sys_breed", "长白猪", "长白猪", 11, '{"species":"pig"}'),
    ("sys_breed", "杜长大三元猪", "杜长大三元猪", 12, '{"species":"pig"}'),
    ("sys_breed", "黑土猪", "黑土猪", 13, '{"species":"pig"}'),
]


def init_dict_data(db: Session) -> None:
    """初始化字典数据（仅首次执行，已有数据则跳过）"""
    if db.query(DictType).count() > 0:
        return

    for name, dtype, remark in DICT_TYPES:
        db.add(DictType(dict_name=name, dict_type=dtype, status=1, remark=remark))

    for dtype, label, value, sort, extra in DICT_DATA:
        db.add(DictData(dict_type=dtype, dict_label=label, dict_value=value,
                        dict_sort=sort, dict_extra=extra, status=1))

    db.commit()
    print(f"[init] 已初始化字典数据：{len(DICT_TYPES)} 个类型，{len(DICT_DATA)} 条数据")


# ============================================================
# 用户管理（超管视角，场主/员工/超管统一管理）
# ============================================================

def _user_role_map(db: Session, user_ids: list[int]) -> dict[int, list[str]]:
    """按用户ID分组返回角色名列表"""
    if not user_ids:
        return {}
    rows = db.query(SysUserRole, SysRole).join(
        SysRole, SysRole.id == SysUserRole.role_id
    ).filter(
        SysUserRole.user_id.in_(user_ids),
        SysUserRole.deleted == False,
        SysRole.deleted == False,
    ).all()
    result: dict[int, list[str]] = {}
    for ur, role in rows:
        result.setdefault(ur.user_id, []).append(role.role_name)
    return result


def list_users(db: Session, query: UserQuery) -> dict:
    q = db.query(User).filter(User.deleted == False)
    if query.username:
        q = q.filter(User.username.like(f"%{query.username}%"))
    if query.real_name:
        q = q.filter(User.real_name.like(f"%{query.real_name}%"))
    if query.phone:
        q = q.filter(User.phone.like(f"%{query.phone}%"))
    if query.user_type is not None:
        q = q.filter(User.user_type == query.user_type)
    if query.farm_id:
        q = q.filter(User.farm_id == query.farm_id)
    if query.status is not None:
        q = q.filter(User.status == query.status)

    total = q.count()
    users = q.order_by(User.id).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()

    farm_ids = {u.farm_id for u in users if u.farm_id}
    farms = {f.id: f.farm_name for f in db.query(Farm).filter(
        Farm.id.in_(farm_ids), Farm.deleted == False).all()} if farm_ids else {}
    role_map = _user_role_map(db, [u.id for u in users])

    items = [{
        "id": u.id, "username": u.username, "real_name": u.real_name,
        "phone": u.phone, "user_type": u.user_type, "farm_id": u.farm_id,
        "farm_name": farms.get(u.farm_id) if u.farm_id else None,
        "post": u.post, "status": u.status,
        "role_names": role_map.get(u.id, []),
        "create_time": u.create_time,
    } for u in users]
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def add_user(db: Session, body: UserIn) -> User:
    if db.query(User).filter(User.username == body.username, User.deleted == False).first():
        raise BizException("账号已存在", code=40040)
    user = User(
        username=body.username,
        password=hash_password(body.password),
        real_name=body.real_name,
        phone=body.phone,
        user_type=body.user_type,
        farm_id=body.farm_id,
        post=body.post,
        status=body.status,
    )
    db.add(user)
    db.flush()
    if body.role_ids:
        for rid in set(body.role_ids):
            db.add(SysUserRole(user_id=user.id, role_id=rid))
    elif body.user_type == 3:
        # 员工未手动指定角色时，按岗位自动关联默认角色（RBAC）
        assign_role_by_post(db, user.id, body.post)
    db.commit()
    return user


def update_user(db: Session, user_id: int, body: UserUpdateIn) -> User:
    user = db.query(User).filter(User.id == user_id, User.deleted == False).first()
    if not user:
        raise BizException("用户不存在", code=40041)
    data = body.model_dump(exclude_unset=True)
    pwd = data.pop("password", None)
    role_ids = data.pop("role_ids", None)
    for k, v in data.items():
        setattr(user, k, v)
    if pwd:
        user.password = hash_password(pwd)
    if role_ids is not None:
        _replace_user_roles(db, user_id, role_ids)
    db.commit()
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = db.query(User).filter(User.id == user_id, User.deleted == False).first()
    if not user:
        raise BizException("用户不存在", code=40041)
    if user.user_type == 1:
        raise BizException("超级管理员账号不允许删除", code=40042)
    user.deleted = True
    db.query(SysUserRole).filter(SysUserRole.user_id == user_id, SysUserRole.deleted == False).update(
        {SysUserRole.deleted: True}, synchronize_session=False
    )
    db.commit()


def reset_password(db: Session, user_id: int, new_password: str) -> None:
    user = db.query(User).filter(User.id == user_id, User.deleted == False).first()
    if not user:
        raise BizException("用户不存在", code=40041)
    user.password = hash_password(new_password)
    db.commit()


def _replace_user_roles(db: Session, user_id: int, role_ids: list[int]) -> None:
    """重置用户角色：旧关联逻辑删除，新关联插入"""
    db.query(SysUserRole).filter(SysUserRole.user_id == user_id, SysUserRole.deleted == False).update(
        {SysUserRole.deleted: True}, synchronize_session=False
    )
    for rid in set(role_ids):
        db.add(SysUserRole(user_id=user_id, role_id=rid))


def assign_roles(db: Session, user_id: int, role_ids: list[int]) -> None:
    if not db.query(User).filter(User.id == user_id, User.deleted == False).first():
        raise BizException("用户不存在", code=40041)
    _replace_user_roles(db, user_id, role_ids)
    db.commit()


def list_user_role_ids(db: Session, user_id: int) -> list[int]:
    rows = db.query(SysUserRole).filter(
        SysUserRole.user_id == user_id, SysUserRole.deleted == False
    ).all()
    return [r.role_id for r in rows]


# ============================================================
# 角色管理
# ============================================================

def list_roles(db: Session, query: RoleQuery) -> dict:
    q = db.query(SysRole).filter(SysRole.deleted == False)
    if query.role_name:
        q = q.filter(SysRole.role_name.like(f"%{query.role_name}%"))
    if query.status is not None:
        q = q.filter(SysRole.status == query.status)
    total = q.count()
    items = q.order_by(SysRole.sort, SysRole.id).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def add_role(db: Session, body: RoleIn) -> SysRole:
    if db.query(SysRole).filter(SysRole.role_key == body.role_key, SysRole.deleted == False).first():
        raise BizException(f"角色权限标识 {body.role_key} 已存在", code=40043)
    role = SysRole(**body.model_dump())
    db.add(role)
    db.commit()
    return role


def update_role(db: Session, role_id: int, body: RoleUpdateIn) -> SysRole:
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.deleted == False).first()
    if not role:
        raise BizException("角色不存在", code=40044)
    data = body.model_dump(exclude_unset=True)
    if "role_key" in data and data["role_key"] != role.role_key:
        exists = db.query(SysRole).filter(
            SysRole.role_key == data["role_key"], SysRole.deleted == False
        ).first()
        if exists:
            raise BizException(f"角色权限标识 {data['role_key']} 已存在", code=40043)
    for k, v in data.items():
        setattr(role, k, v)
    db.commit()
    return role


def delete_role(db: Session, role_id: int) -> None:
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.deleted == False).first()
    if not role:
        raise BizException("角色不存在", code=40044)
    cnt = db.query(SysUserRole).filter(
        SysUserRole.role_id == role_id, SysUserRole.deleted == False
    ).count()
    if cnt > 0:
        raise BizException(f"该角色已分配给 {cnt} 个用户，无法删除", code=40045)
    role.deleted = True
    db.commit()


# ============================================================
# 菜单管理（RBAC，P3-4 用）
# ============================================================

def list_menus(db: Session, query: MenuQuery) -> list:
    """返回菜单树（含 children）"""
    q = db.query(SysMenu).filter(SysMenu.deleted == False)
    if query.menu_name:
        q = q.filter(SysMenu.menu_name.like(f"%{query.menu_name}%"))
    if query.status is not None:
        q = q.filter(SysMenu.status == query.status)
    menus = q.order_by(SysMenu.sort, SysMenu.id).all()

    nodes: dict[int, dict] = {}
    for m in menus:
        nodes[m.id] = {
            "id": m.id, "parent_id": m.parent_id, "menu_name": m.menu_name,
            "menu_type": m.menu_type, "path": m.path, "component": m.component,
            "perms": m.perms, "icon": m.icon, "sort": m.sort,
            "visible": m.visible, "status": m.status, "children": [],
        }
    roots = []
    for m in menus:
        node = nodes[m.id]
        if m.parent_id and m.parent_id in nodes:
            nodes[m.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


def add_menu(db: Session, body: MenuIn) -> SysMenu:
    menu = SysMenu(**body.model_dump())
    db.add(menu)
    db.commit()
    return menu


def update_menu(db: Session, menu_id: int, body: MenuUpdateIn) -> SysMenu:
    menu = db.query(SysMenu).filter(SysMenu.id == menu_id, SysMenu.deleted == False).first()
    if not menu:
        raise BizException("菜单不存在", code=40046)
    data = body.model_dump(exclude_unset=True)
    if "parent_id" in data and data["parent_id"] == menu.id:
        raise BizException("父菜单不能是自身", code=40047)
    for k, v in data.items():
        setattr(menu, k, v)
    db.commit()
    return menu


def delete_menu(db: Session, menu_id: int) -> None:
    menu = db.query(SysMenu).filter(SysMenu.id == menu_id, SysMenu.deleted == False).first()
    if not menu:
        raise BizException("菜单不存在", code=40046)
    child_cnt = db.query(SysMenu).filter(
        SysMenu.parent_id == menu_id, SysMenu.deleted == False
    ).count()
    if child_cnt > 0:
        raise BizException(f"该菜单下有 {child_cnt} 个子菜单，请先删除子菜单", code=40048)
    menu.deleted = True
    db.commit()


# ============================================================
# 登录日志 / 操作日志
# ============================================================

def record_login_log(db: Session, username: str, user_id: int | None = None,
                     ip: str | None = None, browser: str | None = None,
                     os: str | None = None, status: int = 1,
                     msg: str | None = None) -> None:
    db.add(LoginLog(username=username, user_id=user_id, ip=ip, browser=browser,
                    os=os, status=status, msg=msg, login_time=datetime.now()))
    db.commit()


def record_oper_log(db: Session, title: str, business_type: str, method: str,
                    oper_url: str, oper_user_id: int | None, oper_name: str | None,
                    oper_ip: str | None, status: int = 1, error_msg: str | None = None) -> None:
    db.add(OperLog(title=title, business_type=business_type, method=method,
                   oper_url=oper_url, oper_user_id=oper_user_id, oper_name=oper_name,
                   oper_ip=oper_ip, status=status, error_msg=error_msg,
                   oper_time=datetime.now()))
    db.commit()


def list_login_log(db: Session, query: LogQuery) -> dict:
    q = db.query(LoginLog).filter(LoginLog.deleted == False)
    if query.username:
        q = q.filter(LoginLog.username.like(f"%{query.username}%"))
    if query.status is not None:
        q = q.filter(LoginLog.status == query.status)
    if query.date_start:
        q = q.filter(LoginLog.login_time >= query.date_start)
    if query.date_end:
        q = q.filter(LoginLog.login_time <= query.date_end)
    total = q.count()
    items = q.order_by(LoginLog.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def clear_login_log(db: Session) -> None:
    db.query(LoginLog).filter(LoginLog.deleted == False).delete(synchronize_session=False)
    db.commit()


def list_oper_log(db: Session, query: LogQuery) -> dict:
    q = db.query(OperLog).filter(OperLog.deleted == False)
    if query.username:
        q = q.filter(OperLog.oper_name.like(f"%{query.username}%"))
    if query.status is not None:
        q = q.filter(OperLog.status == query.status)
    if query.date_start:
        q = q.filter(OperLog.oper_time >= query.date_start)
    if query.date_end:
        q = q.filter(OperLog.oper_time <= query.date_end)
    total = q.count()
    items = q.order_by(OperLog.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def clear_oper_log(db: Session) -> None:
    db.query(OperLog).filter(OperLog.deleted == False).delete(synchronize_session=False)
    db.commit()


# ============================================================
# 通知公告
# ============================================================

def list_notices(db: Session, query: NoticeQuery) -> dict:
    q = db.query(SysNotice).filter(SysNotice.deleted == False)
    if query.notice_title:
        q = q.filter(SysNotice.notice_title.like(f"%{query.notice_title}%"))
    if query.notice_type:
        q = q.filter(SysNotice.notice_type == query.notice_type)
    if query.status is not None:
        q = q.filter(SysNotice.status == query.status)
    total = q.count()
    items = q.order_by(SysNotice.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def list_published_notices(db: Session) -> list:
    """已发布的公告列表（首页/登录后展示用）"""
    return db.query(SysNotice).filter(
        SysNotice.deleted == False, SysNotice.status == 1
    ).order_by(SysNotice.id.desc()).limit(10).all()


def get_notice(db: Session, notice_id: int) -> SysNotice:
    notice = db.query(SysNotice).filter(
        SysNotice.id == notice_id, SysNotice.deleted == False
    ).first()
    if not notice:
        raise BizException("公告不存在", code=40049)
    return notice


def add_notice(db: Session, body: NoticeIn, create_by: str) -> SysNotice:
    notice = SysNotice(**body.model_dump(), create_by=create_by)
    db.add(notice)
    db.commit()
    return notice


def update_notice(db: Session, notice_id: int, body: NoticeUpdateIn) -> SysNotice:
    notice = get_notice(db, notice_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(notice, k, v)
    db.commit()
    return notice


def delete_notice(db: Session, notice_id: int) -> None:
    notice = get_notice(db, notice_id)
    notice.deleted = True
    db.commit()


# ============================================================
# RBAC（P3-4）
# ============================================================

# 全部业务模块（权限标识 = 模块 key，前端菜单/后端接口共用）
RBAC_MODULES = [
    "dashboard", "farm", "pen", "animal", "feeding",
    "inventory", "health", "breeding", "review", "finance",
    "system", "statistics",
]

# 角色 → 允许访问的模块
ROLE_PERMS = {
    "admin": RBAC_MODULES,
    "owner": [m for m in RBAC_MODULES if m != "system"],
    "feeder": ["dashboard", "pen", "animal", "feeding"],
    "vet": ["dashboard", "pen", "animal", "health", "inventory"],
    "breeder": ["dashboard", "pen", "animal", "breeding"],
    "keeper": ["dashboard", "pen", "inventory"],
}

# 预置角色：(role_name, role_key, sort)
RBAC_ROLES = [
    ("超级管理员", "admin", 1),
    ("养殖场主", "owner", 2),
    ("饲喂员", "feeder", 3),
    ("兽医", "vet", 4),
    ("繁育员", "breeder", 5),
    ("库管员", "keeper", 6),
]

# 岗位 → 默认角色 key（新增员工时自动关联）
POST_ROLE_MAP = {
    "饲喂员": "feeder",
    "兽医": "vet",
    "繁育员": "breeder",
    "库管员": "keeper",
}

# 预置目录菜单：(perms, parent_id, menu_name, menu_type, path, icon, sort)
RBAC_MENUS = [
    ("dashboard", 0, "数据大屏", "M", "/dashboard", "DataAnalysis", 1),
    ("farm", 0, "养殖场管理", "M", "/farm", "OfficeBuilding", 2),
    ("pen", 0, "圈舍管理", "M", "/pen", "Grid", 3),
    ("animal", 0, "档案管理", "M", "/animal", "Notebook", 4),
    ("feeding", 0, "饲喂管理", "M", "/feeding", "Food", 5),
    ("inventory", 0, "物资库存", "M", "/inventory", "Box", 6),
    ("health", 0, "防疫诊疗", "M", "/health", "FirstAidKit", 7),
    ("breeding", 0, "繁育管理", "M", "/breeding", "Connection", 8),
    ("review", 0, "审核中心", "M", "/review", "Stamp", 9),
    ("finance", 0, "销售财务", "M", "/finance", "Money", 10),
    ("system", 0, "系统管理", "M", "/system", "Setting", 11),
    ("statistics", 0, "统计分析", "M", "/statistics", "TrendCharts", 12),
]


def init_rbac_data(db: Session) -> None:
    """初始化 RBAC 数据（角色 + 目录菜单），仅首次执行"""
    if db.query(SysRole).count() > 0:
        return
    for name, key, sort in RBAC_ROLES:
        db.add(SysRole(role_name=name, role_key=key, sort=sort, status=1,
                       perms=json.dumps(ROLE_PERMS[key], ensure_ascii=False),
                       remark=f"{name}角色（RBAC 预置）"))
    for perms, parent, name, mtype, path, icon, sort in RBAC_MENUS:
        db.add(SysMenu(parent_id=parent, menu_name=name, menu_type=mtype,
                       path=path, perms=perms, icon=icon, sort=sort, visible=1, status=1))
    db.commit()
    print(f"[init] 已初始化 RBAC 数据：{len(RBAC_ROLES)} 个角色，{len(RBAC_MENUS)} 个菜单")


def assign_role_by_post(db: Session, user_id: int, post: str | None) -> None:
    """给员工按岗位关联默认角色（岗位映射不到角色则跳过）"""
    if not post:
        return
    role_key = POST_ROLE_MAP.get(post)
    if not role_key:
        return
    role = db.query(SysRole).filter(SysRole.role_key == role_key, SysRole.deleted == False).first()
    if not role:
        return
    exists = db.query(SysUserRole).filter(
        SysUserRole.user_id == user_id, SysUserRole.role_id == role.id,
        SysUserRole.deleted == False,
    ).first()
    if not exists:
        db.add(SysUserRole(user_id=user_id, role_id=role.id))
        db.commit()


def sync_employee_roles(db: Session, user_id: int, new_post: str | None) -> None:
    """员工岗位变化时：移除旧的岗位默认角色，按新岗位关联默认角色"""
    role_keys = list(POST_ROLE_MAP.values())
    role_ids = [r.id for r in db.query(SysRole).filter(
        SysRole.role_key.in_(role_keys), SysRole.deleted == False).all()]
    if role_ids:
        db.query(SysUserRole).filter(
            SysUserRole.user_id == user_id,
            SysUserRole.role_id.in_(role_ids),
            SysUserRole.deleted == False,
        ).update({SysUserRole.deleted: True}, synchronize_session=False)
    db.commit()
    assign_role_by_post(db, user_id, new_post)


def get_user_role_keys(db: Session, user_id: int) -> list[str]:
    rows = db.query(SysUserRole, SysRole).join(
        SysRole, SysRole.id == SysUserRole.role_id
    ).filter(
        SysUserRole.user_id == user_id, SysUserRole.deleted == False,
        SysRole.deleted == False, SysRole.status == 1,
    ).all()
    return [role.role_key for _, role in rows]


def get_user_perms(db: Session, user_id: int) -> set[str]:
    """当前用户的权限模块集合。超管拥有全部；场主拥有全部业务模块（不含 system）；员工按角色 perms。"""
    user = db.query(User).filter(User.id == user_id, User.deleted == False).first()
    if not user:
        return set()
    if user.user_type == 1:
        return set(RBAC_MODULES)
    if user.user_type == 2:
        return {m for m in RBAC_MODULES if m != "system"}
    rows = db.query(SysUserRole, SysRole).join(
        SysRole, SysRole.id == SysUserRole.role_id
    ).filter(
        SysUserRole.user_id == user_id, SysUserRole.deleted == False,
        SysRole.deleted == False, SysRole.status == 1,
    ).all()
    perms: set[str] = set()
    for _, role in rows:
        if role.perms:
            try:
                perms.update(json.loads(role.perms))
            except (ValueError, TypeError):
                pass
    return perms


def get_user_menus(db: Session, user_id: int) -> list[dict]:
    """用户可见的目录菜单树（按权限过滤，前端可据此渲染）"""
    perms = get_user_perms(db, user_id)
    menus = db.query(SysMenu).filter(
        SysMenu.deleted == False, SysMenu.status == 1,
    ).order_by(SysMenu.sort, SysMenu.id).all()
    nodes: dict[int, dict] = {}
    for m in menus:
        nodes[m.id] = {
            "id": m.id, "parent_id": m.parent_id, "menu_name": m.menu_name,
            "menu_type": m.menu_type, "path": m.path, "perms": m.perms,
            "icon": m.icon, "children": [],
        }
    roots = []
    for m in menus:
        node = nodes[m.id]
        if m.parent_id and m.parent_id in nodes:
            nodes[m.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return [r for r in roots if not r["perms"] or r["perms"] in perms]


# ============================================================
# 站内消息（缺口6：审核结果通知闭环）
# ============================================================

def send_message(db: Session, farm_id: int, receiver_user_id: int, title: str,
                 content: str = None, related_module: str = None, related_id: int = None,
                 message_type: str = "审核结果") -> SysMessage:
    """发送站内消息（不 commit，由调用方统一提交）"""
    msg = SysMessage(
        farm_id=farm_id, receiver_user_id=receiver_user_id,
        message_type=message_type, title=title, content=content,
        related_module=related_module, related_id=related_id, is_read=0,
    )
    db.add(msg)
    return msg


def list_messages(db: Session, user_id: int, is_read: int = None,
                  page_num: int = 1, page_size: int = 10) -> dict:
    """我的站内消息列表（仅本人，分页 + 已读筛选）"""
    q = db.query(SysMessage).filter(
        SysMessage.receiver_user_id == user_id, SysMessage.deleted == False
    )
    if is_read is not None:
        q = q.filter(SysMessage.is_read == is_read)
    total = q.count()
    items = q.order_by(SysMessage.create_time.desc(), SysMessage.id.desc()).offset(
        (page_num - 1) * page_size
    ).limit(page_size).all()
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def unread_message_count(db: Session, user_id: int) -> int:
    """未读消息数（顶栏角标）"""
    return db.query(SysMessage).filter(
        SysMessage.receiver_user_id == user_id,
        SysMessage.is_read == 0,
        SysMessage.deleted == False,
    ).count()


def mark_message_read(db: Session, user_id: int, message_id: int) -> SysMessage:
    """标记单条已读（只能操作自己的消息）"""
    msg = db.query(SysMessage).filter(
        SysMessage.id == message_id,
        SysMessage.receiver_user_id == user_id,
        SysMessage.deleted == False,
    ).first()
    if not msg:
        raise BizException("消息不存在", code=40310)
    if msg.is_read == 0:
        msg.is_read = 1
        msg.read_time = datetime.now()
    db.commit()
    return msg


def mark_all_messages_read(db: Session, user_id: int) -> int:
    """全部标记已读，返回更新条数"""
    rows = db.query(SysMessage).filter(
        SysMessage.receiver_user_id == user_id,
        SysMessage.is_read == 0,
        SysMessage.deleted == False,
    ).all()
    now = datetime.now()
    for m in rows:
        m.is_read = 1
        m.read_time = now
    db.commit()
    return len(rows)
