"""
认证路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import Result
from app.schemas.auth import LoginIn, OwnerRegisterIn, EmployeeRegisterIn
from app.schemas.common import TokenOut
from app.services import auth_service

router = APIRouter()


@router.post("/login", summary="登录")
def login(body: LoginIn, db: Session = Depends(get_db)):
    token = auth_service.login(db, body)
    return Result.ok(data=token)


@router.post("/register/owner", summary="养殖场主注册")
def register_owner(body: OwnerRegisterIn, db: Session = Depends(get_db)):
    result = auth_service.register_owner(db, body)
    return Result.ok(data=result, msg="注册成功")


@router.post("/register/employee", summary="员工注册")
def register_employee(body: EmployeeRegisterIn, db: Session = Depends(get_db)):
    result = auth_service.register_employee(db, body)
    return Result.ok(data=result, msg="注册成功")
