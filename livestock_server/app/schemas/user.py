"""
用户相关 schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserOut(BaseModel):
    """用户信息返回"""
    id: int
    username: str
    real_name: str
    phone: str
    user_type: int
    farm_id: Optional[int] = None
    post: Optional[str] = None
    status: int
    create_time: Optional[datetime] = None

    # 让 Pydantic 支持从 ORM 对象读取（不是只读 dict）
    class Config:
        from_attributes = True
