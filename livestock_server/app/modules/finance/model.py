"""
销售财务 ORM 模型

四张表（salary_config 已在 salary 模块）：
- SaleOrder：销售订单（出栏销售，一条订单多只）
- SaleOrderDetail：销售明细（单只：饲养天数/各项成本/利润）
- CostExpense：成本支出（饲料/兽药/疫苗/人工/水电/其他）
- SalaryRecord：员工薪资记录（按月发放）

出栏成本分摊算法（对应 DBD 8.2 sp_calc_animal_total_cost，service 层实现）：
- feed_cost：按耳标所在圈舍的饲喂记录成本累加（feed_date 在入栏~出栏之间）
- medicine_cost：防疫/诊疗用药成本（当前物资表无单价，置 0，注释说明）
- labor_cost：按月薪 × 饲养天数 / 30 分摊
- total_cost = feed + medicine + labor + consumable
"""
from sqlalchemy import Column, String, Integer, Date, DateTime, Numeric

from app.models.base import BasePO


class SaleOrder(BasePO):
    """销售订单表"""
    __tablename__ = "sale_order"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    order_no = Column(String(32), nullable=False, unique=True, comment="订单编号：SO+yyyyMMdd+流水")
    customer = Column(String(100), nullable=False, index=True, comment="客户名称")
    customer_phone = Column(String(20), nullable=True, comment="客户电话")
    animal_count = Column(Integer, nullable=False, default=0, comment="销售数量")
    total_weight = Column(Numeric(10, 2), nullable=False, default=0, comment="总重量 kg")
    unit_price = Column(Numeric(10, 2), nullable=False, comment="单价 元/kg")
    total_amount = Column(Numeric(12, 2), nullable=False, default=0, comment="总销售额")
    order_date = Column(DateTime, nullable=False, index=True, comment="订单时间")
    settle_status = Column(String(10), nullable=False, default="未结算", comment="结算状态：已结算/未结算")
    settle_time = Column(DateTime, nullable=True, comment="结算时间")
    species = Column(String(10), nullable=True, comment="养殖种类")
    remark = Column(String(255), nullable=True, comment="备注")


class SaleOrderDetail(BasePO):
    """销售明细表"""
    __tablename__ = "sale_order_detail"

    order_id = Column(Integer, nullable=False, index=True, comment="销售订单ID")
    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    ear_tag = Column(String(10), nullable=False, index=True, comment="耳标")
    archive_id = Column(Integer, nullable=True, comment="档案ID")
    species = Column(String(10), nullable=False, comment="养殖种类")
    breed = Column(String(50), nullable=True, comment="品种")
    weight = Column(Numeric(8, 2), nullable=False, comment="销售重量 kg")
    raise_days = Column(Integer, nullable=True, comment="饲养天数")
    feed_cost = Column(Numeric(12, 2), nullable=True, comment="饲料成本")
    medicine_cost = Column(Numeric(12, 2), nullable=True, comment="药品疫苗成本")
    labor_cost = Column(Numeric(12, 2), nullable=True, comment="分摊人工成本")
    consumable_cost = Column(Numeric(12, 2), nullable=True, comment="分摊耗材成本")
    total_cost = Column(Numeric(12, 2), nullable=True, comment="饲养总成本")
    sale_amount = Column(Numeric(12, 2), nullable=True, comment="销售收入")
    profit = Column(Numeric(12, 2), nullable=True, comment="单只利润")
    profit_rate = Column(Numeric(6, 2), nullable=True, comment="利润率 %")
    remark = Column(String(255), nullable=True, comment="备注")


class CostExpense(BasePO):
    """成本支出表"""
    __tablename__ = "cost_expense"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    expense_type = Column(String(20), nullable=False, index=True, comment="支出类型：饲料/兽药/疫苗/人工/水电/其他")
    amount = Column(Numeric(12, 2), nullable=False, comment="支出金额")
    expense_date = Column(Date, nullable=False, index=True, comment="支出日期")
    related_material_id = Column(Integer, nullable=True, comment="关联物资ID")
    related_order_id = Column(Integer, nullable=True, comment="关联销售订单ID")
    related_user_id = Column(Integer, nullable=True, comment="关联用户ID（人工成本）")
    voucher_no = Column(String(50), nullable=True, comment="凭证号")
    remark = Column(String(255), nullable=True, comment="备注")


class SalaryRecord(BasePO):
    """员工薪资记录表"""
    __tablename__ = "salary_record"

    farm_id = Column(Integer, nullable=False, index=True, comment="养殖场ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    post = Column(String(20), nullable=False, comment="岗位")
    pay_month = Column(String(7), nullable=False, index=True, comment="工资月份 yyyy-MM")
    base_salary = Column(Numeric(10, 2), nullable=False, comment="基础薪资")
    bonus = Column(Numeric(10, 2), nullable=False, default=0, comment="奖金")
    deduct = Column(Numeric(10, 2), nullable=False, default=0, comment="扣款")
    actual_pay = Column(Numeric(10, 2), nullable=False, comment="实发金额")
    pay_time = Column(DateTime, nullable=True, comment="发放时间")
    status = Column(String(10), nullable=False, default="待发放", comment="状态：待发放/已发放")
    remark = Column(String(255), nullable=True, comment="备注")
