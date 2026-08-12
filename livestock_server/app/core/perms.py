"""
RBAC 权限依赖（P3-4）

用法：
    @router.post("/feeding/record/add", summary="新增饲喂记录")
    def add_record(..., _: None = Depends(require_perms("feeding"))):
        ...

员工按岗位关联角色（sys_user_role → sys_role.perms）校验模块权限；
超管/场主默认拥有全部模块权限，不受角色配置影响。
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import BizException
from app.database import get_db
from app.models.user import User
from app.modules.system.service import get_user_perms


def require_perms(perm: str):
    """校验当前用户是否拥有某模块权限（perm 为模块 key，如 feeding/health）"""
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        perms = get_user_perms(db, current_user.id)
        if perm not in perms:
            raise BizException("无权限访问该模块", code=40303)
    return dependency
