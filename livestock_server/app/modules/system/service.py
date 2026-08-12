"""
系统管理 service：字典类型 + 字典数据 CRUD + 字典初始化
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.system.model import DictType, DictData
from app.modules.system.schema import (
    DictTypeIn, DictTypeUpdateIn, DictTypeQuery,
    DictDataIn, DictDataUpdateIn, DictDataQuery,
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
    # 品种
    ("sys_breed", "荷斯坦", "荷斯坦", 1, '{"species":"cattle"}'),
    ("sys_breed", "安格斯", "安格斯", 2, '{"species":"cattle"}'),
    ("sys_breed", "西门塔尔", "西门塔尔", 3, '{"species":"cattle"}'),
    ("sys_breed", "黄牛", "黄牛", 4, '{"species":"cattle"}'),
    ("sys_breed", "杜泊", "杜泊", 5, '{"species":"sheep"}'),
    ("sys_breed", "小尾寒羊", "小尾寒羊", 6, '{"species":"sheep"}'),
    ("sys_breed", "湖羊", "湖羊", 7, '{"species":"sheep"}'),
    ("sys_breed", "长白", "长白", 8, '{"species":"pig"}'),
    ("sys_breed", "大约克", "大约克", 9, '{"species":"pig"}'),
    ("sys_breed", "杜洛克", "杜洛克", 10, '{"species":"pig"}'),
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
