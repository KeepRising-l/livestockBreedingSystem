"""
依赖注入模块

定义 FastAPI 依赖项：
- get_current_user：从请求头解析 JWT，返回当前用户对象
- 要求登录的接口用 Depends(get_current_user)

超管切换养殖场机制：
- 超管登录后，前端通过请求头 X-Farm-Id 指定要操作的养殖场
- get_current_user 检测到超管 + X-Farm-Id 时，把返回的 user 对象的 farm_id 临时替换
- 用 object.__setattr__ 绕过 SQLAlchemy 的属性 instrumentation，
  避免污染 session dirty 状态（请求结束 db.close() 后就丢弃，不会写库）
"""
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import BizException
from app.models.user import User


def get_current_user(
    authorization: str = Header(None, description="Bearer {token}"),
    x_farm_id: int = Header(None, alias="X-Farm-Id", description="超管切换养殖场用"),
    db: Session = Depends(get_db),
) -> User:
    """
    从请求头解析 token，返回当前登录用户对象。

    使用方式：
        @router.get("/xxx")
        def xxx(current_user: User = Depends(get_current_user)):
            ...

    超管支持：
        超管本身没有 farm_id，前端通过 X-Farm-Id 请求头指定要操作的养殖场。
        这里检测到超管 + X-Farm-Id 后，把返回的 user.farm_id 临时替换为该值，
        这样所有现有的 current_user.farm_id 代码无需修改即可支持超管切换。
    """
    if not authorization:
        raise BizException("未登录或 token 缺失", code=401)

    # 期望格式：Bearer xxxxxx
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise BizException("token 格式错误，应为 Bearer {token}", code=401)

    token = parts[1]
    payload = decode_access_token(token)
    if payload is None:
        raise BizException("token 无效或已过期", code=401)

    user_id = payload.get("sub")
    if not user_id:
        raise BizException("token 中缺少用户信息", code=401)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise BizException("用户不存在", code=401)

    if user.status != 1:
        raise BizException("账号已被禁用", code=401)

    # 超管切换养殖场：用 X-Farm-Id 头覆盖 user.farm_id
    if user.user_type == 1 and x_farm_id and x_farm_id > 0:
        # 用 object.__setattr__ 绕过 SQLAlchemy 属性机制，避免污染 session dirty
        object.__setattr__(user, "farm_id", x_farm_id)

    return user


def resolve_farm_id(current_user: User, x_farm_id: int | None = None) -> int:
    """
    解析目标养殖场 ID（保留兼容，新代码直接用 current_user.farm_id 即可）：

    - 超管（user_type=1）：如果请求头传了 X-Farm-Id 就用它，否则返回 0
    - 普通用户（user_type=2/3）：直接返回自己的 farm_id，忽略 X-Farm-Id
    """
    if current_user.user_type == 1:
        if x_farm_id is not None and x_farm_id > 0:
            return x_farm_id
        return 0
    return current_user.farm_id or 0
