"""
认证路由
"""
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import BizException
from app.database import get_db
from app.core.response import Result
from app.models.user import User
from app.schemas.auth import LoginIn, OwnerRegisterIn
from app.schemas.common import TokenOut
from app.services import auth_service
from app.modules.system import service as system_service

router = APIRouter()

# 登录防爆破（进程内限流，uvicorn 单 worker 部署下有效；多 worker 需改用 Redis）
_LOGIN_FAIL_LIMIT = 5       # 窗口内允许的最大失败次数
_LOGIN_FAIL_WINDOW = 900    # 窗口时长（秒）
_login_fails: dict[str, list[float]] = defaultdict(list)


def _login_rate_key(ip: str | None, username: str) -> str:
    return f"{ip or 'unknown'}:{username}"


def _check_login_rate(key: str) -> None:
    now = time.time()
    fails = _login_fails.get(key)
    if fails:
        _login_fails[key] = [t for t in fails if now - t < _LOGIN_FAIL_WINDOW]
        if len(_login_fails[key]) >= _LOGIN_FAIL_LIMIT:
            raise BizException("失败次数过多，请 15 分钟后再试", code=42901)


def _record_login_fail(key: str) -> None:
    _login_fails[key].append(time.time())


def _parse_ua(ua: str) -> tuple[str, str]:
    """从 user-agent 粗略解析浏览器与操作系统"""
    ua = ua or ""
    if "Windows" in ua:
        os = "Windows"
    elif "Mac" in ua:
        os = "macOS"
    elif "Android" in ua:
        os = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os = "iOS"
    elif "Linux" in ua:
        os = "Linux"
    else:
        os = "其他"
    if "Edg/" in ua:
        browser = "Edge"
    elif "Chrome/" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua:
        browser = "Safari"
    else:
        browser = "其他"
    return browser, os


@router.post("/login", summary="登录")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    browser, os = _parse_ua(request.headers.get("user-agent", ""))
    rate_key = _login_rate_key(ip, body.username)
    _check_login_rate(rate_key)
    try:
        token = auth_service.login(db, body)
    except BizException as e:
        _record_login_fail(rate_key)
        system_service.record_login_log(
            db, body.username, ip=ip, browser=browser, os=os,
            status=0, msg=str(e.msg)[:200],
        )
        raise
    _login_fails.pop(rate_key, None)  # 登录成功清零失败计数
    system_service.record_login_log(
        db, body.username, ip=ip, browser=browser, os=os,
        status=1, msg="登录成功",
    )
    return Result.ok(data=token)


@router.get("/permissions", summary="当前用户权限（角色/权限模块/可见菜单，RBAC P3-4）")
def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    roles = system_service.get_user_role_keys(db, current_user.id)
    perms = system_service.get_user_perms(db, current_user.id)
    menus = system_service.get_user_menus(db, current_user.id)
    return Result.ok(data={
        "user_id": current_user.id,
        "username": current_user.username,
        "user_type": current_user.user_type,
        "farm_id": current_user.farm_id,
        "post": current_user.post,
        "roles": roles,
        "perms": sorted(perms),
        "menus": menus,
    })


@router.post("/register/owner", summary="养殖场主注册")
def register_owner(body: OwnerRegisterIn, db: Session = Depends(get_db)):
    result = auth_service.register_owner(db, body)
    return Result.ok(data=result, msg="注册成功")
