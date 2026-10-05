"""
物资库存模块 DTO
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============ 库存 ============

class MaterialStockIn(BaseModel):
    """新增库存物资（首次入库时建立档案，后续走进货增加数量）"""
    material_type: str = Field(..., description="物资类型：饲料/疫苗/兽药")
    material_name: str = Field(..., max_length=100, description="物资名称")
    specification: Optional[str] = Field(None, max_length=100, description="规格型号")
    quantity: float = Field(0, ge=0, description="初始库存数量")
    unit: str = Field("kg", max_length=10, description="单位：kg/瓶/盒/袋")
    unit_price: Optional[float] = Field(None, ge=0, description="初始库存单价（元/单位，后续以进货均价为准）")
    warning_threshold: Optional[float] = Field(None, description="缺货预警阈值")
    production_date: Optional[date] = Field(None, description="生产日期")
    expiry_date: Optional[date] = Field(None, description="有效期")
    manager_user_id: Optional[int] = Field(None, description="负责人ID")
    remark: Optional[str] = Field(None, max_length=255)


class MaterialStockIncreaseIn(BaseModel):
    """管理端增加库存（免审：直接生成一条已通过的进货记录并立即同步库存）"""
    material_type: str = Field(..., description="物资类型：饲料/疫苗/兽药")
    material_name: str = Field(..., max_length=100, description="物资名称（可下拉选已有，也可输入新物资）")
    quantity: float = Field(..., gt=0, description="进货数量")
    unit: str = Field("kg", max_length=10, description="单位")
    cost_price: Optional[float] = Field(None, gt=0, description="进货单价（元），不填则库存均价保持不变")
    batch_no: Optional[str] = Field(None, max_length=50, description="批次号")
    supplier: Optional[str] = Field(None, max_length=100, description="供应商")
    purchase_date: date = Field(default_factory=date.today, description="进货日期")
    production_date: Optional[date] = Field(None, description="生产日期")
    expiry_date: Optional[date] = Field(None, description="有效期")
    remark: Optional[str] = Field(None, max_length=255)


class MaterialStockUpdateIn(BaseModel):
    """修改库存物资基本信息（数量不在此处改，走进货/领用）"""
    specification: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = Field(None, ge=0, description="库存均价（元/单位），留空不修改")
    warning_threshold: Optional[float] = None
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    manager_user_id: Optional[int] = None
    remark: Optional[str] = None


class MaterialStockOut(BaseModel):
    id: int
    farm_id: int
    material_type: str
    material_name: str
    specification: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    warning_threshold: Optional[float] = None
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    is_shortage: Optional[int] = None
    manager_user_id: Optional[int] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialStockQuery(BaseModel):
    material_type: Optional[str] = None
    material_name: Optional[str] = None
    status: Optional[str] = None
    is_shortage: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 进货 ============

class MaterialPurchaseIn(BaseModel):
    """进货（员工提交，待审核；审核通过后自动增加库存）"""
    material_type: str = Field(..., description="物资类型：饲料/疫苗/兽药")
    material_name: str = Field(..., max_length=100, description="物资名称")
    specification: Optional[str] = Field(None, description="规格型号（如果库存里没有此物资，会自动创建）")
    batch_no: Optional[str] = Field(None, max_length=50, description="批次号")
    quantity: float = Field(..., gt=0, description="进货数量")
    unit: str = Field("kg", max_length=10, description="单位")
    cost_price: float = Field(..., gt=0, description="进货单价（元）")
    production_date: Optional[date] = Field(None, description="生产日期")
    expiry_date: Optional[date] = Field(None, description="有效期")
    supplier: Optional[str] = Field(None, max_length=100, description="供应商")
    purchase_date: date = Field(..., description="进货日期")
    remark: Optional[str] = Field(None, max_length=255)


class MaterialPurchaseUpdateIn(BaseModel):
    """修改进货记录（仅待审核可改）"""
    batch_no: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    cost_price: Optional[float] = Field(None, gt=0)
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier: Optional[str] = None
    remark: Optional[str] = None


class MaterialPurchaseOut(BaseModel):
    id: int
    farm_id: int
    stock_id: Optional[int] = None
    material_type: str
    material_name: str
    batch_no: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = None
    total_cost: Optional[float] = None
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier: Optional[str] = None
    purchase_date: date
    audit_status: str
    operator_user_id: Optional[int] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialPurchaseQuery(BaseModel):
    material_type: Optional[str] = None
    material_name: Optional[str] = None
    purchase_date_start: Optional[date] = None
    purchase_date_end: Optional[date] = None
    audit_status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 领用 ============

class MaterialConsumeIn(BaseModel):
    """领用（员工提交，待审核；审核通过后自动扣减库存）"""
    stock_id: int = Field(..., description="库存ID（必须指定是哪种物资）")
    batch_no: Optional[str] = Field(None, max_length=50, description="批次号")
    quantity: float = Field(..., gt=0, description="领用数量")
    unit: str = Field("kg", max_length=10, description="单位")
    consume_date: date = Field(..., description="领用日期")
    related_module: Optional[str] = Field(None, description="关联模块：饲喂/防疫/诊疗")
    related_id: Optional[int] = Field(None, description="关联业务记录ID")
    remark: Optional[str] = Field(None, max_length=255)


class MaterialConsumeUpdateIn(BaseModel):
    """修改领用记录（仅待审核可改）"""
    batch_no: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    consume_date: Optional[date] = None
    related_module: Optional[str] = None
    related_id: Optional[int] = None
    remark: Optional[str] = None


class MaterialConsumeOut(BaseModel):
    id: int
    farm_id: int
    stock_id: Optional[int] = None
    material_type: str
    material_name: str
    batch_no: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    consume_date: date
    related_module: Optional[str] = None
    related_id: Optional[int] = None
    status: Optional[str] = None
    audit_status: str
    consumer_user_id: Optional[int] = None
    consumer_name: Optional[str] = Field(None, description="领用人姓名（= 提交人）")
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialConsumeQuery(BaseModel):
    material_type: Optional[str] = None
    material_name: Optional[str] = None
    stock_id: Optional[int] = None
    consume_date_start: Optional[date] = None
    consume_date_end: Optional[date] = None
    audit_status: Optional[str] = None
    related_module: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10


class AuditActionIn(BaseModel):
    """审核动作（与饲喂模块共用相同结构）"""
    audit_status: str = Field(..., description="目标审核状态：通过/驳回")
    remark: Optional[str] = Field(None, description="审核备注")
