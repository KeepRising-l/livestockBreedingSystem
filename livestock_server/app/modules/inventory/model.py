"""
物资库存模块 ORM 模型

三张表：
- MaterialStock：库存表（饲料/疫苗/兽药的当前库存量、有效期、状态）
- MaterialPurchase：进货记录表（每次进货一条，审核通过后增加库存）
- MaterialConsume：领用记录表（每次领用一条，审核通过后扣减库存）

状态自动维护：
- 库存 status：根据 expiry_date 实时计算（正常/即将过期/已过期）
- 库存 is_shortage：quantity < warning_threshold 时为 1
- 进货/领用记录 audit_status：待审核 → 通过/驳回
"""
from datetime import date

from sqlalchemy import Column, String, Integer, Date, Numeric, Boolean, UniqueConstraint

from app.models.base import BasePO


class MaterialStock(BasePO):
    """物资库存表"""
    __tablename__ = "material_stock"
    __table_args__ = (
        # 同一养殖场下，物资类型+名称唯一
        UniqueConstraint("farm_id", "material_type", "material_name", name="uk_farm_type_name"),
    )

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    material_type = Column(String(10), nullable=False, index=True, comment="物资类型：饲料/疫苗/兽药")
    material_name = Column(String(100), nullable=False, index=True, comment="物资名称")
    specification = Column(String(100), nullable=True, comment="规格型号")
    quantity = Column(Numeric(12, 2), nullable=False, default=0, comment="库存数量")
    unit = Column(String(10), nullable=False, default="kg", comment="单位：kg/瓶/盒/袋")
    warning_threshold = Column(Numeric(12, 2), nullable=True, comment="缺货预警阈值")
    production_date = Column(Date, nullable=True, comment="生产日期")
    expiry_date = Column(Date, nullable=True, index=True, comment="有效期")
    status = Column(String(10), default="正常", comment="状态：正常/即将过期/已过期")
    is_shortage = Column(Integer, default=0, comment="是否缺货：0否 1是")
    manager_user_id = Column(Integer, nullable=True, comment="负责人ID")
    remark = Column(String(255), nullable=True, comment="备注")


class MaterialPurchase(BasePO):
    """进货记录表"""
    __tablename__ = "material_purchase"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    stock_id = Column(Integer, nullable=True, index=True, comment="关联库存ID")
    material_type = Column(String(10), nullable=False, comment="物资类型")
    material_name = Column(String(100), nullable=False, comment="物资名称")
    batch_no = Column(String(50), nullable=True, comment="批次号")
    quantity = Column(Numeric(12, 2), nullable=False, comment="进货数量")
    unit = Column(String(10), nullable=False, default="kg", comment="单位")
    cost_price = Column(Numeric(10, 2), nullable=False, comment="进货单价")
    total_cost = Column(Numeric(12, 2), nullable=True, comment="进货总金额")
    production_date = Column(Date, nullable=True, comment="生产日期")
    expiry_date = Column(Date, nullable=True, comment="有效期")
    supplier = Column(String(100), nullable=True, comment="供应商")
    purchase_date = Column(Date, nullable=False, index=True, comment="进货日期")
    audit_status = Column(String(10), default="待审核", comment="审核状态：待审核/通过/驳回")
    operator_user_id = Column(Integer, nullable=True, comment="操作人ID")
    remark = Column(String(255), nullable=True, comment="备注")


class MaterialConsume(BasePO):
    """领用记录表"""
    __tablename__ = "material_consume"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    stock_id = Column(Integer, nullable=True, index=True, comment="关联库存ID")
    material_type = Column(String(10), nullable=False, comment="物资类型")
    material_name = Column(String(100), nullable=False, comment="物资名称")
    batch_no = Column(String(50), nullable=True, comment="批次号")
    quantity = Column(Numeric(12, 2), nullable=False, comment="领用数量")
    unit = Column(String(10), nullable=False, default="kg", comment="单位")
    consume_date = Column(Date, nullable=False, index=True, comment="领用日期")
    related_module = Column(String(20), nullable=True, comment="关联模块：饲喂/防疫/诊疗")
    related_id = Column(Integer, nullable=True, comment="关联业务记录ID")
    status = Column(String(10), default="成功", comment="状态：成功/失败")
    audit_status = Column(String(10), default="待审核", comment="审核状态：待审核/通过/驳回")
    consumer_user_id = Column(Integer, nullable=True, comment="领用人ID")
    remark = Column(String(255), nullable=True, comment="备注")
