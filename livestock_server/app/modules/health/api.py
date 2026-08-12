"""
防疫诊疗路由

- 防疫记录：新增单条 + 批量新增（同一疫苗类型 + 多耳标）、列表、详情、修改、删除、审核
- 诊疗记录：新增、列表、详情、修改、删除、审核
- 员工提交进入待审核；审核动作仅场主/超管可执行
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.core.deps import get_current_user
from app.core.exceptions import BizException
from app.models.user import User
from app.modules.inventory.schema import AuditActionIn
from app.modules.health import service as health_service
from app.modules.health.schema import (
    VaccineRecordIn, VaccineBatchIn, VaccineRecordUpdateIn, VaccineRecordOut, VaccineRecordQuery,
    MedicalRecordIn, MedicalRecordUpdateIn, MedicalRecordOut, MedicalRecordQuery,
)

router = APIRouter()


def _check_owner(current_user: User):
    """养殖场主或超管能审核（user_type=1 或 2）"""
    if current_user.user_type not in (1, 2):
        raise BizException("无权限操作，需养殖场主权限", code=40301)
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)


# ============================================================
# 防疫记录
# ============================================================

@router.get("/vaccine/list", summary="防疫记录列表")
def list_vaccines(
    vaccine_date_start: date = Query(None),
    vaccine_date_end: date = Query(None),
    ear_tag: str = Query(None),
    vaccine_type: str = Query(None),
    species: str = Query(None),
    audit_status: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = VaccineRecordQuery(
        vaccine_date_start=vaccine_date_start, vaccine_date_end=vaccine_date_end,
        ear_tag=ear_tag, vaccine_type=vaccine_type, species=species,
        audit_status=audit_status, pageNum=pageNum, pageSize=pageSize,
    )
    result = health_service.list_vaccines(db, current_user.farm_id, query)
    result["list"] = [VaccineRecordOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/vaccine/{record_id}", summary="防疫记录详情")
def get_vaccine(record_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    rec = health_service.get_vaccine(db, current_user.farm_id, record_id)
    return Result.ok(data=VaccineRecordOut.model_validate(rec))


@router.post("/vaccine/add", summary="新增防疫记录（单条，员工提交进入待审核）")
def add_vaccine(body: VaccineRecordIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    rec = health_service.add_vaccine(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=VaccineRecordOut.model_validate(rec), msg="提交成功，等待审核")


@router.post("/vaccine/batch-add", summary="批量新增防疫记录（同一疫苗类型 + 多个耳标）")
def batch_add_vaccines(body: VaccineBatchIn, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    records = health_service.batch_add_vaccines(db, current_user.farm_id, body, current_user.id)
    result = {"total": len(records), "list": [VaccineRecordOut.model_validate(r) for r in records]}
    return Result.ok(data=result, msg=f"批量提交成功，共 {len(records)} 条，等待审核")


@router.put("/vaccine/update/{record_id}", summary="修改防疫记录（仅待审核可改）")
def update_vaccine(record_id: int, body: VaccineRecordUpdateIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    rec = health_service.update_vaccine(db, current_user.farm_id, record_id, body)
    return Result.ok(data=VaccineRecordOut.model_validate(rec), msg="修改成功")


@router.delete("/vaccine/{record_id}", summary="删除防疫记录（已通过不能删）")
def delete_vaccine(record_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    health_service.delete_vaccine(db, current_user.farm_id, record_id)
    return Result.ok(msg="删除成功")


@router.post("/vaccine/audit/{record_id}", summary="审核防疫记录（场主权限）")
def audit_vaccine(record_id: int, body: AuditActionIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    rec = health_service.audit_record(db, current_user.farm_id, "vaccine", record_id, body.audit_status)
    return Result.ok(data=VaccineRecordOut.model_validate(rec), msg=f"已{body.audit_status}")


# ============================================================
# 诊疗记录
# ============================================================

@router.get("/medical/list", summary="诊疗记录列表")
def list_medicals(
    medical_date_start: date = Query(None),
    medical_date_end: date = Query(None),
    ear_tag: str = Query(None),
    disease_type: str = Query(None),
    species: str = Query(None),
    treatment_status: str = Query(None),
    audit_status: str = Query(None),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    query = MedicalRecordQuery(
        medical_date_start=medical_date_start, medical_date_end=medical_date_end,
        ear_tag=ear_tag, disease_type=disease_type, species=species,
        treatment_status=treatment_status, audit_status=audit_status,
        pageNum=pageNum, pageSize=pageSize,
    )
    result = health_service.list_medicals(db, current_user.farm_id, query)
    result["list"] = [MedicalRecordOut.model_validate(r) for r in result["list"]]
    return Result.ok(data=result)


@router.get("/medical/{record_id}", summary="诊疗记录详情")
def get_medical(record_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    rec = health_service.get_medical(db, current_user.farm_id, record_id)
    return Result.ok(data=MedicalRecordOut.model_validate(rec))


@router.post("/medical/add", summary="新增诊疗记录（员工提交进入待审核）")
def add_medical(body: MedicalRecordIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    if not current_user.farm_id:
        raise BizException("当前用户未关联养殖场", code=40300)
    rec = health_service.add_medical(db, current_user.farm_id, body, current_user.id)
    return Result.ok(data=MedicalRecordOut.model_validate(rec), msg="提交成功，等待审核")


@router.put("/medical/update/{record_id}", summary="修改诊疗记录（仅待审核可改）")
def update_medical(record_id: int, body: MedicalRecordUpdateIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    rec = health_service.update_medical(db, current_user.farm_id, record_id, body)
    return Result.ok(data=MedicalRecordOut.model_validate(rec), msg="修改成功")


@router.delete("/medical/{record_id}", summary="删除诊疗记录（已通过不能删）")
def delete_medical(record_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    health_service.delete_medical(db, current_user.farm_id, record_id)
    return Result.ok(msg="删除成功")


@router.post("/medical/audit/{record_id}", summary="审核诊疗记录（场主权限）")
def audit_medical(record_id: int, body: AuditActionIn, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    _check_owner(current_user)
    rec = health_service.audit_record(db, current_user.farm_id, "medical", record_id, body.audit_status)
    return Result.ok(data=MedicalRecordOut.model_validate(rec), msg=f"已{body.audit_status}")
