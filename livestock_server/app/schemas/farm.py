"""
养殖场相关 schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FarmOut(BaseModel):
    """养殖场信息返回"""
    id: int
    farm_name: str
    owner_user_id: int
    phone: Optional[str] = None
    livestock_types: str
    address: Optional[str] = None
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class FarmUpdateIn(BaseModel):
    """养殖场信息更新"""
    farm_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)


class FarmListOut(BaseModel):
    """养殖场列表项（超管下拉选择用）"""
    id: int
    farm_name: str
    livestock_types: str

    class Config:
        from_attributes = True
