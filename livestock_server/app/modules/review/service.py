"""
审核业务逻辑

统一审核入口：聚合查询五类业务的待审核记录 + 转发审核到各模块。
- 待审核来源：feeding_record / material_purchase / material_consume / vaccine_record / medical_record
- 不新增业务表，审核状态直接落各业务表的 audit_status
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.models.user import User
from app.modules.feeding.model import FeedingRecord
from app.modules.feeding.schema import AuditActionIn as FeedingAuditIn
from app.modules.feeding import service as feeding_service
from app.modules.inventory.model import MaterialPurchase, MaterialConsume
from app.modules.inventory import service as inventory_service
from app.modules.health.model import VaccineRecord, MedicalRecord
from app.modules.health import service as health_service
from app.modules.system import service as system_service
from app.modules.review.schema import ReviewItemOut, ReviewAuditIn

# 业务类型配置：类型 → (中文名, 列表查询函数, 单条摘要函数, 操作人字段)
BUSINESS_NAMES = {
    "feeding": "饲喂记录",
    "purchase": "进货记录",
    "consume": "领用记录",
    "vaccine": "防疫记录",
    "medical": "诊疗记录",
}


def _feeding_item(rec: FeedingRecord) -> ReviewItemOut:
    pen = f"{rec.pen_type or ''}{rec.pen_id}号圈舍"
    summary = f"{rec.feed_date} {rec.time_period}班 · {pen} · 饲喂{rec.animal_count or 0}头"
    return ReviewItemOut(
        business_type="feeding", business_name=BUSINESS_NAMES["feeding"],
        id=rec.id, create_time=rec.create_time, operator_user_id=rec.operator_user_id,
        summary=summary,
        detail={"feed_date": str(rec.feed_date), "time_period": rec.time_period,
                "pen_id": rec.pen_id, "animal_count": rec.animal_count,
                "feed_cost": float(rec.feed_cost) if rec.feed_cost else None,
                "remark": rec.remark},
    )


def _purchase_item(rec: MaterialPurchase) -> ReviewItemOut:
    summary = f"进货 {rec.material_name} × {rec.quantity}{rec.unit} · 单价{rec.cost_price}元"
    return ReviewItemOut(
        business_type="purchase", business_name=BUSINESS_NAMES["purchase"],
        id=rec.id, create_time=rec.create_time, operator_user_id=rec.operator_user_id,
        summary=summary,
        detail={"purchase_date": str(rec.purchase_date), "material_type": rec.material_type,
                "material_name": rec.material_name, "quantity": float(rec.quantity),
                "unit": rec.unit, "supplier": rec.supplier, "remark": rec.remark},
    )


def _consume_item(rec: MaterialConsume) -> ReviewItemOut:
    module = rec.related_module or "其他"
    summary = f"领用 {rec.material_name} × {rec.quantity}{rec.unit} · {module}"
    return ReviewItemOut(
        business_type="consume", business_name=BUSINESS_NAMES["consume"],
        id=rec.id, create_time=rec.create_time, operator_user_id=rec.consumer_user_id,
        summary=summary,
        detail={"consume_date": str(rec.consume_date), "material_type": rec.material_type,
                "material_name": rec.material_name, "quantity": float(rec.quantity),
                "unit": rec.unit, "related_module": module, "remark": rec.remark},
    )


def _vaccine_item(rec: VaccineRecord) -> ReviewItemOut:
    summary = f"防疫 {rec.ear_tag} · {rec.vaccine_type}"
    return ReviewItemOut(
        business_type="vaccine", business_name=BUSINESS_NAMES["vaccine"],
        id=rec.id, create_time=rec.create_time, operator_user_id=rec.operator_user_id,
        summary=summary,
        detail={"vaccine_date": str(rec.vaccine_date), "ear_tag": rec.ear_tag,
                "species": rec.species, "vaccine_type": rec.vaccine_type,
                "vaccine_name": rec.vaccine_name, "dosage": rec.dosage, "remark": rec.remark},
    )


def _medical_item(rec: MedicalRecord) -> ReviewItemOut:
    summary = f"诊疗 {rec.ear_tag} · {rec.disease_type}"
    return ReviewItemOut(
        business_type="medical", business_name=BUSINESS_NAMES["medical"],
        id=rec.id, create_time=rec.create_time, operator_user_id=rec.operator_user_id,
        summary=summary,
        detail={"medical_date": str(rec.medical_date), "ear_tag": rec.ear_tag,
                "species": rec.species, "disease_type": rec.disease_type,
                "medicine": rec.medicine, "treatment_status": rec.treatment_status,
                "remark": rec.remark},
    )


def _query_pending(db: Session, farm_id: int, business_type: str, page_num: int = 1, page_size: int = 10) -> List:
    """查某类型的待审核记录，返回映射好的 ReviewItemOut 列表"""
    if business_type == "feeding":
        q = db.query(FeedingRecord).filter(
            FeedingRecord.farm_id == farm_id, FeedingRecord.audit_status == "待审核",
            FeedingRecord.deleted == False,
        )
        total = q.count()
        rows = q.order_by(FeedingRecord.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        return [_feeding_item(r) for r in rows], total
    if business_type == "purchase":
        q = db.query(MaterialPurchase).filter(
            MaterialPurchase.farm_id == farm_id, MaterialPurchase.audit_status == "待审核",
            MaterialPurchase.deleted == False,
        )
        total = q.count()
        rows = q.order_by(MaterialPurchase.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        return [_purchase_item(r) for r in rows], total
    if business_type == "consume":
        q = db.query(MaterialConsume).filter(
            MaterialConsume.farm_id == farm_id, MaterialConsume.audit_status == "待审核",
            MaterialConsume.deleted == False,
        )
        total = q.count()
        rows = q.order_by(MaterialConsume.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        return [_consume_item(r) for r in rows], total
    if business_type == "vaccine":
        q = db.query(VaccineRecord).filter(
            VaccineRecord.farm_id == farm_id, VaccineRecord.audit_status == "待审核",
            VaccineRecord.deleted == False,
        )
        total = q.count()
        rows = q.order_by(VaccineRecord.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        return [_vaccine_item(r) for r in rows], total
    if business_type == "medical":
        q = db.query(MedicalRecord).filter(
            MedicalRecord.farm_id == farm_id, MedicalRecord.audit_status == "待审核",
            MedicalRecord.deleted == False,
        )
        total = q.count()
        rows = q.order_by(MedicalRecord.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        return [_medical_item(r) for r in rows], total
    raise BizException("不支持的业务类型", code=40201)


def _fill_operator_names(db: Session, items: List[ReviewItemOut]):
    """批量填充提交人姓名"""
    ids = {it.operator_user_id for it in items if it.operator_user_id}
    if not ids:
        return
    users = db.query(User).filter(User.id.in_(ids)).all()
    name_map = {u.id: u.real_name or u.username for u in users}
    for it in items:
        it.operator_name = name_map.get(it.operator_user_id) if it.operator_user_id else None


def list_pending(db: Session, farm_id: int, business_type: str, page_num: int, page_size: int) -> dict:
    """单类型待审核列表（分页）"""
    items, total = _query_pending(db, farm_id, business_type, page_num, page_size)
    _fill_operator_names(db, items)
    return {"list": items, "total": total, "pageNum": page_num, "pageSize": page_size}


def list_all_pending(db: Session, farm_id: int, limit: int = 50) -> dict:
    """全部待审核（聚合各类型，按提交时间倒序）"""
    all_items: List[ReviewItemOut] = []
    for bt in BUSINESS_NAMES:
        items, _ = _query_pending(db, farm_id, bt, 1, limit)
        all_items.extend(items)
    all_items.sort(key=lambda x: x.create_time or datetime.min, reverse=True)
    all_items = all_items[:limit]
    _fill_operator_names(db, all_items)
    return {"list": all_items, "total": len(all_items)}


def counts(db: Session, farm_id: int) -> dict:
    """各类型待审核数量统计"""
    result = {}
    for bt in BUSINESS_NAMES:
        items, total = _query_pending(db, farm_id, bt, 1, 1)
        result[bt] = total
    result["total"] = sum(result.values())
    return result


def _get_submitter_id(db: Session, farm_id: int, business_type: str, business_id: int) -> Optional[int]:
    """查询待审核记录的提交人（缺口6：审核后通知提交人）"""
    if business_type == "feeding":
        rec = db.query(FeedingRecord).filter(
            FeedingRecord.id == business_id, FeedingRecord.farm_id == farm_id,
            FeedingRecord.deleted == False,
        ).first()
        return rec.operator_user_id if rec else None
    if business_type == "purchase":
        rec = db.query(MaterialPurchase).filter(
            MaterialPurchase.id == business_id, MaterialPurchase.farm_id == farm_id,
            MaterialPurchase.deleted == False,
        ).first()
        return rec.operator_user_id if rec else None
    if business_type == "consume":
        rec = db.query(MaterialConsume).filter(
            MaterialConsume.id == business_id, MaterialConsume.farm_id == farm_id,
            MaterialConsume.deleted == False,
        ).first()
        return rec.consumer_user_id if rec else None
    if business_type == "vaccine":
        rec = db.query(VaccineRecord).filter(
            VaccineRecord.id == business_id, VaccineRecord.farm_id == farm_id,
            VaccineRecord.deleted == False,
        ).first()
        return rec.operator_user_id if rec else None
    if business_type == "medical":
        rec = db.query(MedicalRecord).filter(
            MedicalRecord.id == business_id, MedicalRecord.farm_id == farm_id,
            MedicalRecord.deleted == False,
        ).first()
        return rec.operator_user_id if rec else None
    return None


def audit(db: Session, farm_id: int, body: ReviewAuditIn, user_id: int) -> dict:
    """统一审核：转发到各模块的审核逻辑 + 审核结果通知提交人（缺口6）"""
    if body.audit_status not in ("通过", "驳回"):
        raise BizException("审核状态只能填：通过 / 驳回", code=40202)
    if body.business_type not in BUSINESS_NAMES:
        raise BizException("不支持的业务类型", code=40201)

    # 先取提交人（各模块 audit 会 commit，需在转发前查询）
    submitter_id = _get_submitter_id(db, farm_id, body.business_type, body.business_id)

    remark = body.remark
    if body.business_type in ("feeding", "purchase", "consume"):
        audit_body = FeedingAuditIn(audit_status=body.audit_status, remark=remark)
        if body.business_type == "feeding":
            feeding_service.audit_record(db, farm_id, body.business_id, audit_body)
        elif body.business_type == "purchase":
            inventory_service.audit_purchase(db, farm_id, body.business_id, audit_body)
        else:
            inventory_service.audit_consume(db, farm_id, body.business_id, audit_body)
    else:
        record_type = body.business_type  # vaccine / medical
        health_service.audit_record(db, farm_id, record_type, body.business_id, body.audit_status)

    # 审核结果通知（缺口6）：通知提交人（自己审核自己的记录不发给自己）
    if submitter_id and submitter_id != user_id:
        business_name = BUSINESS_NAMES.get(body.business_type, "业务")
        result_word = "通过" if body.audit_status == "通过" else "被驳回"
        content = f"您提交的{business_name}（ID:{body.business_id}）已{result_word}"
        if remark:
            content += f"，审核备注：{remark}"
        system_service.send_message(
            db, farm_id, submitter_id,
            title=f"{business_name}审核{result_word}",
            content=content,
            related_module=body.business_type,
            related_id=body.business_id,
        )
        db.commit()

    return {
        "business_type": body.business_type,
        "business_id": body.business_id,
        "audit_status": body.audit_status,
    }
