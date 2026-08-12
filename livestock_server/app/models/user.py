"""
用户模型

三类用户：
- user_type=1：超级管理员（系统级，不归属任何养殖场）
- user_type=2：养殖场主管理员（farm_id 关联自己创建的养殖场）
- user_type=3：养殖场员工（farm_id 关联所就职的养殖场）
"""
from sqlalchemy import Column, String, Integer, Boolean

from app.models.base import BasePO


class User(BasePO):
    __tablename__ = "sys_user"

    username = Column(String(50), unique=True, nullable=False, comment="登录账号")
    password = Column(String(200), nullable=False, comment="密码哈希")
    real_name = Column(String(50), nullable=False, comment="真实姓名")
    phone = Column(String(20), nullable=False, comment="手机号")
    user_type = Column(Integer, nullable=False, default=3, comment="用户类型：1超级管理员 2养殖场主 3员工")
    farm_id = Column(Integer, nullable=True, comment="所属养殖场ID（超级管理员为空）")
    post = Column(String(50), nullable=True, comment="员工岗位：饲喂员/兽医/繁育员/库管员")
    status = Column(Integer, default=1, comment="状态：1启用 0禁用")
