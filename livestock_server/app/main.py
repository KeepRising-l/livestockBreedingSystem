"""
FastAPI 应用入口

启动方式（在 livestock_server 目录下）：
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

或者直接运行本文件：
    python -m app.main
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import (
    BizException, biz_exception_handler,
    validation_exception_handler, global_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from app.api.v1 import router as v1_router
from app.database import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403  引入所有模型，确保建表能发现
from app.core.security import hash_password, decode_access_token
from app.models.user import User
from app.modules.system.service import init_dict_data, init_rbac_data, record_oper_log
from app.scheduler import start_scheduler, shutdown_scheduler


def _ensure_sys_role_perms(db):
    """老库 sys_role 表无 perms 列时补一列（MySQL；SQLite 测试库由 create_all 建新表，走异常忽略）"""
    from sqlalchemy import text
    try:
        rows = db.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME='sys_role' AND COLUMN_NAME='perms'"
        )).fetchall()
        if not rows:
            db.execute(text("ALTER TABLE sys_role ADD COLUMN perms TEXT"))
            db.commit()
            print("[init] 已为 sys_role 表补充 perms 列")
    except Exception:
        pass


def init_db():
    """
    初始化数据库：
    1. 自动建表（开发期用，生产环境建议用 alembic 迁移）
    2. 创建超级管理员账号（如果不存在）
    3. 初始化字典 / RBAC 角色菜单（首次）
    """
    # 自动建表（已存在的表不会被覆盖，安全）
    Base.metadata.create_all(bind=engine)

    # 初始化超级管理员
    db = SessionLocal()
    try:
        _ensure_sys_role_perms(db)
        admin = db.query(User).filter(User.username == settings.SUPER_ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=settings.SUPER_ADMIN_USERNAME,
                password=hash_password(settings.SUPER_ADMIN_PASSWORD),
                real_name="超级管理员",
                phone=settings.SUPER_ADMIN_PHONE,
                user_type=1,    # 超级管理员
                farm_id=None,
                status=1,
            )
            db.add(admin)
            db.commit()
            print(f"[init] 已创建超级管理员：{settings.SUPER_ADMIN_USERNAME} / {settings.SUPER_ADMIN_PASSWORD}")

        # 初始化字典数据（首次启动时）
        init_dict_data(db)
        # 初始化 RBAC 角色 + 菜单（首次启动时）
        init_rbac_data(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动前执行初始化 + 启动定时任务"""
    print(f"[启动] {settings.APP_NAME} 初始化中...")
    init_db()
    start_scheduler()
    print(f"[启动] {settings.APP_NAME} 已就绪，访问 http://127.0.0.1:{settings.APP_PORT}/docs 查看接口文档")
    yield
    shutdown_scheduler()
    print(f"[关闭] {settings.APP_NAME} 已停止")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="智能养殖信息管理系统后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册异常处理器
app.add_exception_handler(BizException, biz_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.middleware("http")
async def oper_log_middleware(request: Request, call_next):
    """操作日志中间件：记录 POST/PUT/DELETE 写请求到 oper_log 表"""
    method = request.method
    path = request.url.path
    if method not in ("POST", "PUT", "DELETE") or not path.startswith("/api/"):
        return await call_next(request)

    # 从 token 解析当前用户
    user_id, user_name = None, None
    auth = request.headers.get("authorization", "")
    try:
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            payload = decode_access_token(parts[1])
            if payload and payload.get("sub"):
                user_id = int(payload["sub"])
    except Exception:
        pass

    response = await call_next(request)

    # 从响应体判断业务成败（BizException 也返回 HTTP 200，需看 body 的 code）
    status, error_msg = 1, None
    try:
        body = getattr(response, "body", None)
        if body:
            data = json.loads(body)
            if data.get("code", 200) != 200:
                status = 0
                error_msg = str(data.get("msg", ""))[:200]
    except Exception:
        pass

    if user_id is not None:
        try:
            db = SessionLocal()
            try:
                if user_name is None:
                    u = db.query(User).filter(User.id == user_id).first()
                    user_name = u.username if u else None
                record_oper_log(
                    db,
                    title=None,
                    business_type={"POST": "add", "PUT": "update", "DELETE": "delete"}.get(method, "other"),
                    method=method,
                    oper_url=path,
                    oper_user_id=user_id,
                    oper_name=user_name,
                    oper_ip=request.client.host if request.client else None,
                    status=status,
                    error_msg=error_msg,
                )
            finally:
                db.close()
        except Exception:
            pass
    return response

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 v1 路由
app.include_router(v1_router, prefix="/api")


@app.get("/", summary="健康检查")
def root():
    return {"status": "ok", "name": settings.APP_NAME, "version": "1.0.0"}


@app.get("/health", summary="健康检查")
def health():
    return {"status": "up"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=(settings.APP_ENV == "dev"),
    )
