"""
防疫诊疗 DTO

- VaccineRecord：防疫记录（含批量新增：同一疫苗类型 + 多个耳标）
- MedicalRecord：诊疗记录
"""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ============ 防疫记录 ============

class VaccineRecordIn(BaseModel):
    """新增单条防疫记录"""
    vaccine_date: date = Field(..., description="防疫日期")
    ear_tag: str = Field(..., max_length=10, description="耳标")
    pen_id: Optional[int] = Field(None, description="圈舍ID")
    species: str = Field(..., max_length=10, description="养殖种类：牛/羊/猪")
    breed: Optional[str] = Field(None, max_length=50, description="品种")
    growth_stage: Optional[str] = Field(None, max_length=20, description="生长阶段")
    vaccine_type: str = Field(..., max_length=50, description="疫苗类型（口蹄疫/布病/小反刍兽疫/猪瘟等）")
    vaccine_name: Optional[str] = Field(None, max_length=100, description="疫苗名称")
    dosage: Optional[str] = Field(None, max_length=50, description="接种剂量")
    next_vaccine_date: Optional[date] = Field(None, description="下次接种日期")
    remark: Optional[str] = Field(None, max_length=255)


class VaccineBatchIn(BaseModel):
    """批量新增防疫记录：同一疫苗类型 + 多个耳标，service 里循环插多行"""
    vaccine_date: date = Field(..., description="防疫日期")
    ear_tags: List[str] = Field(..., min_length=1, description="耳标列表（同一疫苗类型）")
    species: str = Field(..., max_length=10, description="养殖种类：牛/羊/猪")
    breed: Optional[str] = Field(None, max_length=50, description="品种")
    growth_stage: Optional[str] = Field(None, max_length=20, description="生长阶段")
    vaccine_type: str = Field(..., max_length=50, description="疫苗类型")
    vaccine_name: Optional[str] = Field(None, max_length=100, description="疫苗名称")
    dosage: Optional[str] = Field(None, max_length=50, description="接种剂量")
    next_vaccine_date: Optional[date] = Field(None, description="下次接种日期")
    remark: Optional[str] = Field(None, max_length=255)


class VaccineRecordUpdateIn(BaseModel):
    """修改防疫记录（仅待审核可改）"""
    vaccine_date: Optional[date] = None
    pen_id: Optional[int] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    growth_stage: Optional[str] = None
    vaccine_type: Optional[str] = None
    vaccine_name: Optional[str] = None
    dosage: Optional[str] = None
    next_vaccine_date: Optional[date] = None
    remark: Optional[str] = None


class VaccineRecordOut(BaseModel):
    """防疫记录返回"""
    id: int
    farm_id: int
    vaccine_date: date
    ear_tag: str
    pen_id: Optional[int] = None
    species: str
    breed: Optional[str] = None
    growth_stage: Optional[str] = None
    vaccine_type: str
    vaccine_name: Optional[str] = None
    dosage: Optional[str] = None
    next_vaccine_date: Optional[date] = None
    audit_status: str
    operator_user_id: Optional[int] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class VaccineRecordQuery(BaseModel):
    """防疫记录列表查询"""
    vaccine_date_start: Optional[date] = None
    vaccine_date_end: Optional[date] = None
    ear_tag: Optional[str] = None
    vaccine_type: Optional[str] = None
    species: Optional[str] = None
    audit_status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 诊疗记录 ============

class MedicalRecordIn(BaseModel):
    """新增诊疗记录"""
    medical_date: date = Field(..., description="诊疗日期")
    ear_tag: str = Field(..., max_length=10, description="耳标")
    pen_id: Optional[int] = Field(None, description="圈舍ID")
    species: str = Field(..., max_length=10, description="养殖种类：牛/羊/猪")
    breed: Optional[str] = Field(None, max_length=50, description="品种")
    growth_stage: Optional[str] = Field(None, max_length=20, description="生长阶段")
    onset_date: Optional[date] = Field(None, description="发病日期")
    disease_type: str = Field(..., max_length=50, description="病情类型（感冒/腹泻/肺炎/外伤等）")
    symptom: Optional[str] = Field(None, max_length=500, description="主要症状")
    medicine: str = Field(..., max_length=500, description="诊疗用药")
    treatment_plan: Optional[str] = Field(None, max_length=500, description="治疗方案")
    treatment_status: str = Field("治疗中", max_length=10, description="诊疗状态：治疗中/已康复/死亡")
    cure_date: Optional[date] = Field(None, description="康复日期")
    remark: Optional[str] = Field(None, max_length=255)


class MedicalRecordUpdateIn(BaseModel):
    """修改诊疗记录（仅待审核可改）"""
    medical_date: Optional[date] = None
    pen_id: Optional[int] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    growth_stage: Optional[str] = None
    onset_date: Optional[date] = None
    disease_type: Optional[str] = None
    symptom: Optional[str] = None
    medicine: Optional[str] = None
    treatment_plan: Optional[str] = None
    treatment_status: Optional[str] = None
    cure_date: Optional[date] = None
    remark: Optional[str] = None


class MedicalRecordOut(BaseModel):
    """诊疗记录返回"""
    id: int
    farm_id: int
    medical_date: date
    ear_tag: str
    pen_id: Optional[int] = None
    species: str
    breed: Optional[str] = None
    growth_stage: Optional[str] = None
    onset_date: Optional[date] = None
    disease_type: str
    symptom: Optional[str] = None
    medicine: str
    treatment_plan: Optional[str] = None
    treatment_status: str
    cure_date: Optional[date] = None
    audit_status: str
    operator_user_id: Optional[int] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MedicalRecordQuery(BaseModel):
    """诊疗记录列表查询"""
    medical_date_start: Optional[date] = None
    medical_date_end: Optional[date] = None
    ear_tag: Optional[str] = None
    disease_type: Optional[str] = None
    species: Optional[str] = None
    treatment_status: Optional[str] = None
    audit_status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10
