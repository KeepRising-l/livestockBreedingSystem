"""
防疫诊疗业务逻辑

核心业务规则：
1. 防疫记录：员工提交，audit_status 自动 = 待审核；支持批量（同一疫苗类型 + 多个耳标，循环插多行）
2. 诊疗记录：员工提交，audit_status 自动 = 待审核
3. 提交时从 animal_archive 快照耳标对应的 pen_id / breed / growth_stage，可选覆盖
4. 审核流程：场主通过/驳回（后续 review 模块统一入口，先提供单条审核）
"""
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.animal.model import Animal
from app.modules.health.model import VaccineRecord, MedicalRecord
from app.modules.health.schema import (
    VaccineRecordIn, VaccineBatchIn, VaccineRecordUpdateIn, VaccineRecordQuery,
    MedicalRecordIn, MedicalRecordUpdateIn, MedicalRecordQuery,
)

# 疫苗类型白名单（与字典 sys_vaccine_type 保持一致，宽松校验只挡非法值）
VACCINE_TYPES = {"口蹄疫", "布病", "小反刍兽疫", "猪瘟", "蓝耳病", "伪狂犬", "牛结节性皮肤病"}
# 诊疗状态白名单
TREATMENT_STATUSES = {"治疗中", "已康复", "死亡"}
# 养殖种类白名单
SPECIES = {"牛", "羊", "猪"}


# ============================================================
# 防疫记录
# ============================================================

def list_vaccines(db: Session, farm_id: int, query: VaccineRecordQuery) -> dict:
    """防疫记录列表（分页+多条件）"""
    q = db.query(VaccineRecord).filter(
        VaccineRecord.farm_id == farm_id, VaccineRecord.deleted == False
    )
    if query.vaccine_date_start:
        q = q.filter(VaccineRecord.vaccine_date >= query.vaccine_date_start)
    if query.vaccine_date_end:
        q = q.filter(VaccineRecord.vaccine_date <= query.vaccine_date_end)
    if query.ear_tag:
        q = q.filter(VaccineRecord.ear_tag == query.ear_tag)
    if query.vaccine_type:
        q = q.filter(VaccineRecord.vaccine_type == query.vaccine_type)
    if query.species:
        q = q.filter(VaccineRecord.species == query.species)
    if query.audit_status:
        q = q.filter(VaccineRecord.audit_status == query.audit_status)

    total = q.count()
    items = q.order_by(VaccineRecord.vaccine_date.desc(), VaccineRecord.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_vaccine(db: Session, farm_id: int, record_id: int) -> VaccineRecord:
    rec = db.query(VaccineRecord).filter(
        VaccineRecord.id == record_id,
        VaccineRecord.farm_id == farm_id,
        VaccineRecord.deleted == False,
    ).first()
    if not rec:
        raise BizException("防疫记录不存在", code=40080)
    return rec


def _snapshot_animal(db: Session, farm_id: int, ear_tag: str) -> dict:
    """
    从档案快照耳标对应的 pen_id / breed / growth_stage。
    档案不存在时返回空快照（防疫不强制要求档案已建档）。
    """
    animal = db.query(Animal).filter(
        Animal.farm_id == farm_id,
        Animal.ear_tag == ear_tag,
        Animal.deleted == False,
    ).first()
    if not animal:
        return {"pen_id": None, "breed": None, "growth_stage": None}
    return {
        "pen_id": animal.pen_id,
        "breed": animal.breed,
        "growth_stage": animal.growth_stage,
    }


def _validate_vaccine_body(species: str, vaccine_type: str):
    if species not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40081)
    if vaccine_type not in VACCINE_TYPES:
        raise BizException(f"疫苗类型只能是：{'/'.join(sorted(VACCINE_TYPES))}", code=40082)


def add_vaccine(db: Session, farm_id: int, body: VaccineRecordIn, user_id: int) -> VaccineRecord:
    """新增单条防疫记录（员工提交，进入待审核）"""
    _validate_vaccine_body(body.species, body.vaccine_type)
    snap = _snapshot_animal(db, farm_id, body.ear_tag)

    rec = VaccineRecord(
        farm_id=farm_id,
        vaccine_date=body.vaccine_date,
        ear_tag=body.ear_tag,
        pen_id=body.pen_id if body.pen_id is not None else snap["pen_id"],
        species=body.species,
        breed=body.breed if body.breed is not None else snap["breed"],
        growth_stage=body.growth_stage if body.growth_stage is not None else snap["growth_stage"],
        vaccine_type=body.vaccine_type,
        vaccine_name=body.vaccine_name,
        dosage=body.dosage,
        next_vaccine_date=body.next_vaccine_date,
        audit_status="待审核",
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(rec)
    db.commit()
    return rec


def batch_add_vaccines(db: Session, farm_id: int, body: VaccineBatchIn, user_id: int) -> List[VaccineRecord]:
    """批量新增防疫记录：同一疫苗类型 + 多个耳标，service 里循环插多行"""
    _validate_vaccine_body(body.species, body.vaccine_type)

    # 去重校验：同一批耳标不能重复
    ear_tags = list(dict.fromkeys(body.ear_tags))  # 保持顺序去重
    if len(ear_tags) != len(body.ear_tags):
        raise BizException("批量防疫的耳标列表中存在重复耳标", code=40083)

    records = []
    for tag in ear_tags:
        snap = _snapshot_animal(db, farm_id, tag)
        rec = VaccineRecord(
            farm_id=farm_id,
            vaccine_date=body.vaccine_date,
            ear_tag=tag,
            pen_id=snap["pen_id"],
            species=body.species,
            breed=body.breed if body.breed is not None else snap["breed"],
            growth_stage=body.growth_stage if body.growth_stage is not None else snap["growth_stage"],
            vaccine_type=body.vaccine_type,
            vaccine_name=body.vaccine_name,
            dosage=body.dosage,
            next_vaccine_date=body.next_vaccine_date,
            audit_status="待审核",
            operator_user_id=user_id,
            remark=body.remark,
        )
        db.add(rec)
        records.append(rec)

    db.commit()
    return records


def update_vaccine(db: Session, farm_id: int, record_id: int, body: VaccineRecordUpdateIn) -> VaccineRecord:
    """修改防疫记录（仅待审核可改）"""
    rec = get_vaccine(db, farm_id, record_id)
    if rec.audit_status != "待审核":
        raise BizException("已审核的防疫记录不能修改", code=40084)

    data = body.model_dump(exclude_unset=True)
    # 改 species / vaccine_type 时校验白名单
    if "species" in data and data["species"]:
        _validate_vaccine_body(data["species"], data.get("vaccine_type") or rec.vaccine_type)
    if "vaccine_type" in data and data["vaccine_type"]:
        _validate_vaccine_body(data.get("species") or rec.species, data["vaccine_type"])

    for k, v in data.items():
        setattr(rec, k, v)
    db.commit()
    return rec


def delete_vaccine(db: Session, farm_id: int, record_id: int):
    rec = get_vaccine(db, farm_id, record_id)
    if rec.audit_status == "通过":
        raise BizException("已审核通过的防疫记录不能删除", code=40085)
    rec.deleted = True
    db.commit()


# ============================================================
# 诊疗记录
# ============================================================

def list_medicals(db: Session, farm_id: int, query: MedicalRecordQuery) -> dict:
    """诊疗记录列表（分页+多条件）"""
    q = db.query(MedicalRecord).filter(
        MedicalRecord.farm_id == farm_id, MedicalRecord.deleted == False
    )
    if query.medical_date_start:
        q = q.filter(MedicalRecord.medical_date >= query.medical_date_start)
    if query.medical_date_end:
        q = q.filter(MedicalRecord.medical_date <= query.medical_date_end)
    if query.ear_tag:
        q = q.filter(MedicalRecord.ear_tag == query.ear_tag)
    if query.disease_type:
        q = q.filter(MedicalRecord.disease_type == query.disease_type)
    if query.species:
        q = q.filter(MedicalRecord.species == query.species)
    if query.treatment_status:
        q = q.filter(MedicalRecord.treatment_status == query.treatment_status)
    if query.audit_status:
        q = q.filter(MedicalRecord.audit_status == query.audit_status)

    total = q.count()
    items = q.order_by(MedicalRecord.medical_date.desc(), MedicalRecord.id.desc()).offset(
        (query.pageNum - 1) * query.pageSize
    ).limit(query.pageSize).all()
    return {"list": items, "total": total, "pageNum": query.pageNum, "pageSize": query.pageSize}


def get_medical(db: Session, farm_id: int, record_id: int) -> MedicalRecord:
    rec = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.farm_id == farm_id,
        MedicalRecord.deleted == False,
    ).first()
    if not rec:
        raise BizException("诊疗记录不存在", code=40090)
    return rec


def add_medical(db: Session, farm_id: int, body: MedicalRecordIn, user_id: int) -> MedicalRecord:
    """新增诊疗记录（员工提交，进入待审核）"""
    if body.species not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40081)
    if body.treatment_status not in TREATMENT_STATUSES:
        raise BizException(f"诊疗状态只能是：{'/'.join(sorted(TREATMENT_STATUSES))}", code=40091)

    snap = _snapshot_animal(db, farm_id, body.ear_tag)

    rec = MedicalRecord(
        farm_id=farm_id,
        medical_date=body.medical_date,
        ear_tag=body.ear_tag,
        pen_id=body.pen_id if body.pen_id is not None else snap["pen_id"],
        species=body.species,
        breed=body.breed if body.breed is not None else snap["breed"],
        growth_stage=body.growth_stage if body.growth_stage is not None else snap["growth_stage"],
        onset_date=body.onset_date,
        disease_type=body.disease_type,
        symptom=body.symptom,
        medicine=body.medicine,
        treatment_plan=body.treatment_plan,
        treatment_status=body.treatment_status,
        cure_date=body.cure_date,
        audit_status="待审核",
        operator_user_id=user_id,
        remark=body.remark,
    )
    db.add(rec)
    db.commit()
    return rec


def update_medical(db: Session, farm_id: int, record_id: int, body: MedicalRecordUpdateIn) -> MedicalRecord:
    """修改诊疗记录（仅待审核可改）"""
    rec = get_medical(db, farm_id, record_id)
    if rec.audit_status != "待审核":
        raise BizException("已审核的诊疗记录不能修改", code=40092)

    data = body.model_dump(exclude_unset=True)
    if "species" in data and data["species"] and data["species"] not in SPECIES:
        raise BizException(f"养殖种类只能是：{'/'.join(sorted(SPECIES))}", code=40081)
    if "treatment_status" in data and data["treatment_status"] and data["treatment_status"] not in TREATMENT_STATUSES:
        raise BizException(f"诊疗状态只能是：{'/'.join(sorted(TREATMENT_STATUSES))}", code=40091)

    for k, v in data.items():
        setattr(rec, k, v)
    db.commit()
    return rec


def delete_medical(db: Session, farm_id: int, record_id: int):
    rec = get_medical(db, farm_id, record_id)
    if rec.audit_status == "通过":
        raise BizException("已审核通过的诊疗记录不能删除", code=40093)
    rec.deleted = True
    db.commit()


# ============================================================
# 审核（后续 review 模块统一入口，此处先提供单条审核）
# ============================================================

def audit_record(db: Session, farm_id: int, record_type: str, record_id: int, action: str):
    """审核防疫/诊疗记录：通过/驳回"""
    if action not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40094)

    if record_type == "vaccine":
        rec = get_vaccine(db, farm_id, record_id)
    elif record_type == "medical":
        rec = get_medical(db, farm_id, record_id)
    else:
        raise BizException("不支持的记录类型，应为 vaccine / medical", code=40095)

    if rec.audit_status != "待审核":
        raise BizException("该记录已审核，不能重复审核", code=40096)

    rec.audit_status = action
    db.commit()
    return rec
