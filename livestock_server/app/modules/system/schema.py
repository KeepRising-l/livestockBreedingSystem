"""
系统管理 DTO：字典类型 + 字典数据
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ========== 字典类型 ==========
class DictTypeOut(BaseModel):
    id: int
    dict_name: str
    dict_type: str
    status: int
    remark: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictTypeIn(BaseModel):
    dict_name: str = Field(..., description="字典名称")
    dict_type: str = Field(..., description="字典类型（唯一标识）")
    status: int = Field(1, description="状态：1正常 0停用")
    remark: Optional[str] = None


class DictTypeUpdateIn(BaseModel):
    dict_name: Optional[str] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class DictTypeQuery(BaseModel):
    dict_name: Optional[str] = None
    dict_type: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 20


# ========== 字典数据 ==========
class DictDataOut(BaseModel):
    id: int
    dict_type: str
    dict_label: str
    dict_value: str
    dict_sort: int
    dict_extra: Optional[str] = None
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictDataIn(BaseModel):
    dict_type: str = Field(..., description="字典类型")
    dict_label: str = Field(..., description="字典标签")
    dict_value: str = Field(..., description="字典键值")
    dict_sort: int = Field(0, description="排序")
    dict_extra: Optional[str] = Field(None, description="扩展信息 JSON")
    status: int = Field(1, description="状态：1正常 0停用")


class DictDataUpdateIn(BaseModel):
    dict_label: Optional[str] = None
    dict_value: Optional[str] = None
    dict_sort: Optional[int] = None
    dict_extra: Optional[str] = None
    status: Optional[int] = None


class DictDataQuery(BaseModel):
    dict_type: Optional[str] = None
    dict_label: Optional[str] = None
    status: Optional[int] = None
    pageNum: int = 1
    pageSize: int = 50
