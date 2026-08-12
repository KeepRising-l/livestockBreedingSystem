"""
安全模块：密码哈希 + JWT 生成与校验

- 密码使用 bcrypt 加密，不可逆
- JWT 用于接口鉴权，登录后返回 token，前端在请求头携带
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from app.config import settings


def hash_password(password: str) -> str:
    """明文密码 -> bcrypt 哈希值（存数据库）"""
    # bcrypt 要求密码以 bytes 形式传入；bcrypt 自带 salt 生成，无需单独生成
    # bcrypt 有 72 字节限制，超长会报错，这里统一截断
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, extra: Optional[dict] = None) -> str:
    """
    生成 JWT token

    :param subject: 主题，一般是用户 ID
    :param extra: 额外要放进 token 的数据（如角色、农场ID）
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,           # 主题
        "exp": expire,            # 过期时间
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    解析 JWT token，返回 payload 字典；解析失败返回 None
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
