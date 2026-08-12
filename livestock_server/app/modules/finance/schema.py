"""
销售财务 DTO

- 出栏销售：SaleOutIn（客户 + 单价 + 每只耳标/重量）→ 自动算成本/利润
- 销售订单：SaleOrderOut / SaleOrderDetailOut / SaleOrderQuery
- 成本支出：CostExpenseIn / Update / Out / Query
- 利润汇总：ProfitSummaryOut
- 薪资记录：SalaryGenerateIn（按月批量生成）/ SalaryRecordOut / SalaryRecordQuery
"""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ============ 出栏销售 ============

class SaleItemIn(BaseModel):
    """订单明细入参：耳标 + 销售重量"""
    ear_tag: str = Field(..., max_length=10, description="耳标")
    weight: float = Field(..., gt=0, description="销售重量 kg")


class SaleOutIn(BaseModel):
    """出栏销售"""
    customer: str = Field(..., max_length=100, description="客户名称")
    customer_phone: Optional[str] = Field(None, max_length=20, description="客户电话")
    unit_price: float = Field(..., gt=0, description="单价 元/kg")
    order_date: Optional[date] = Field(None, description="订单日期（默认今天）")
    remark: Optional[str] = Field(None, max_length=255, description="备注")
    items: List[SaleItemIn] = Field(..., min_length=1, description="销售明细（耳标+重量）")


class SaleOrderDetailOut(BaseModel):
    """销售明细返回"""
    id: int
    order_id: int
    ear_tag: str
    archive_id: Optional[int] = None
    species: str
    breed: Optional[str] = None
    weight: float
    raise_days: Optional[int] = None
    feed_cost: Optional[float] = None
    medicine_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    consumable_cost: Optional[float] = None
    total_cost: Optional[float] = None
    sale_amount: Optional[float] = None
    profit: Optional[float] = None
    profit_rate: Optional[float] = None

    class Config:
        from_attributes = True


class SaleOrderOut(BaseModel):
    """销售订单返回"""
    id: int
    order_no: str
    customer: str
    customer_phone: Optional[str] = None
    animal_count: int
    total_weight: float
    unit_price: float
    total_amount: float
    order_date: datetime
    settle_status: str
    settle_time: Optional[datetime] = None
    species: Optional[str] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class SaleOrderQuery(BaseModel):
    """销售订单列表查询"""
    order_no: Optional[str] = None
    customer: Optional[str] = None
    species: Optional[str] = None
    settle_status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 成本支出 ============

EXPENSE_TYPES = ("饲料", "兽药", "疫苗", "人工", "水电", "其他")


class CostExpenseIn(BaseModel):
    """新增成本支出"""
    expense_type: str = Field(..., max_length=20, description="支出类型：饲料/兽药/疫苗/人工/水电/其他")
    amount: float = Field(..., gt=0, description="支出金额")
    expense_date: date = Field(..., description="支出日期")
    related_material_id: Optional[int] = Field(None, description="关联物资ID")
    related_order_id: Optional[int] = Field(None, description="关联销售订单ID")
    related_user_id: Optional[int] = Field(None, description="关联用户ID（人工成本）")
    voucher_no: Optional[str] = Field(None, max_length=50, description="凭证号")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class CostExpenseUpdateIn(BaseModel):
    """修改成本支出"""
    expense_type: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    expense_date: Optional[date] = None
    related_material_id: Optional[int] = None
    related_order_id: Optional[int] = None
    related_user_id: Optional[int] = None
    voucher_no: Optional[str] = None
    remark: Optional[str] = None


class CostExpenseOut(BaseModel):
    """成本支出返回"""
    id: int
    farm_id: int
    expense_type: str
    amount: float
    expense_date: date
    related_material_id: Optional[int] = None
    related_order_id: Optional[int] = None
    related_user_id: Optional[int] = None
    voucher_no: Optional[str] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class CostExpenseQuery(BaseModel):
    """成本支出列表查询"""
    expense_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pageNum: int = 1
    pageSize: int = 10


# ============ 利润汇总 ============

class ProfitSummaryOut(BaseModel):
    """利润汇总返回（时间段）"""
    order_count: int = 0
    animal_count: int = 0
    total_amount: float = 0
    total_cost: float = 0
    total_profit: float = 0
    profit_rate: float = 0
    expense_amount: float = 0
    net_profit: float = 0


# ============ 薪资记录 ============

class SalaryGenerateIn(BaseModel):
    """按月生成薪资记录"""
    pay_month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="工资月份 yyyy-MM")


class SalaryRecordOut(BaseModel):
    """薪资记录返回"""
    id: int
    user_id: int
    username: Optional[str] = None
    real_name: Optional[str] = None
    post: str
    pay_month: str
    base_salary: float
    bonus: float
    deduct: float
    actual_pay: float
    pay_time: Optional[datetime] = None
    status: str
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class SalaryRecordQuery(BaseModel):
    """薪资记录列表查询"""
    pay_month: Optional[str] = None
    post: Optional[str] = None
    status: Optional[str] = None
    pageNum: int = 1
    pageSize: int = 10
