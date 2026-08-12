"""
防疫诊疗 ORM 模型

两张表：
- VaccineRecord：防疫记录（疫苗类型 + 耳标，支持批量：同一疫苗类型 + 多个耳标循环插多行）
- MedicalRecord：诊疗记录

审核流程：员工提交 → 待审核 → 场主审批通过/驳回
"""
from sqlalchemy import Column, String, Integer, Date

from app.models.base import BasePO


class VaccineRecord(BasePO):
    """防疫记录表"""
    __tablename__ = "vaccine_record"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    vaccine_date = Column(Date, nullable=False, index=True, comment="防疫日期")
    ear_tag = Column(String(10), nullable=False, index=True, comment="耳标")
    pen_id = Column(Integer, nullable=True, comment="圈舍ID")
    species = Column(String(10), nullable=False, comment="养殖种类：牛/羊/猪")
    breed = Column(String(50), nullable=True, comment="品种")
    growth_stage = Column(String(20), nullable=True, comment="生长阶段")
    vaccine_type = Column(String(50), nullable=False, index=True, comment="疫苗类型（口蹄疫/布病/小反刍兽疫/猪瘟等）")
    vaccine_name = Column(String(100), nullable=True, comment="疫苗名称")
    dosage = Column(String(50), nullable=True, comment="接种剂量")
    next_vaccine_date = Column(Date, nullable=True, comment="下次接种日期")
    audit_status = Column(String(10), default="待审核", comment="审核状态：待审核/通过/驳回")
    operator_user_id = Column(Integer, nullable=True, comment="负责人ID")
    remark = Column(String(255), nullable=True, comment="备注")


class MedicalRecord(BasePO):
    """诊疗记录表"""
    __tablename__ = "medical_record"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    medical_date = Column(Date, nullable=False, index=True, comment="诊疗日期")
    ear_tag = Column(String(10), nullable=False, index=True, comment="耳标")
    pen_id = Column(Integer, nullable=True, comment="圈舍ID")
    species = Column(String(10), nullable=False, comment="养殖种类：牛/羊/猪")
    breed = Column(String(50), nullable=True, comment="品种")
    growth_stage = Column(String(20), nullable=True, comment="生长阶段")
    onset_date = Column(Date, nullable=True, comment="发病日期")
    disease_type = Column(String(50), nullable=False, index=True, comment="病情类型（感冒/腹泻/肺炎/外伤等）")
    symptom = Column(String(500), nullable=True, comment="主要症状")
    medicine = Column(String(500), nullable=False, comment="诊疗用药")
    treatment_plan = Column(String(500), nullable=True, comment="治疗方案")
    treatment_status = Column(String(10), default="治疗中", comment="诊疗状态：治疗中/已康复/死亡")
    cure_date = Column(Date, nullable=True, comment="康复日期")
    audit_status = Column(String(10), default="待审核", comment="审核状态：待审核/通过/驳回")
    operator_user_id = Column(Integer, nullable=True, comment="负责人ID")
    remark = Column(String(255), nullable=True, comment="备注")
