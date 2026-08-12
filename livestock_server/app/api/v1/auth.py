"""
认证路由
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.database import get_db
from app.core.response import Result
from app.schemas.auth import LoginIn, OwnerRegisterIn, EmployeeRegisterIn
from app.schemas.common import TokenOut
from app.services import auth_service
from app.modules.system import service as system_service

router = APIRouter()


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
    try:
        token = auth_service.login(db, body)
    except BizException as e:
        system_service.record_login_log(
            db, body.username, ip=ip, browser=browser, os=os,
            status=0, msg=str(e.msg)[:200],
        )
        raise
    system_service.record_login_log(
        db, body.username, ip=ip, browser=browser, os=os,
        status=1, msg="登录成功",
    )
    return Result.ok(data=token)


@router.post("/register/owner", summary="养殖场主注册")
def register_owner(body: OwnerRegisterIn, db: Session = Depends(get_db)):
    result = auth_service.register_owner(db, body)
    return Result.ok(data=result, msg="注册成功")


@router.post("/register/employee", summary="员工注册")
def register_employee(body: EmployeeRegisterIn, db: Session = Depends(get_db)):
    result = auth_service.register_employee(db, body)
    return Result.ok(data=result, msg="注册成功")
