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


def _ensure_stock_unit_price(db):
    """
    缺口1 轻量迁移：为 material_stock / material_consume 补充 unit_price 列并回填存量数据
    （v1.30 药品疫苗成本核算支持；MySQL 老库补列，新库由 create_all 自动建列）
    """
    from sqlalchemy import text
    try:
        # 1. 补列
        for table, col, ddl in (
            ("material_stock", "unit_price", "ALTER TABLE material_stock ADD COLUMN unit_price NUMERIC(10,2)"),
            ("material_consume", "unit_price", "ALTER TABLE material_consume ADD COLUMN unit_price NUMERIC(10,2)"),
        ):
            rows = db.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_NAME='{table}' AND COLUMN_NAME='{col}'"
            )).fetchall()
            if not rows:
                db.execute(text(ddl))
                print(f"[init] 已为 {table} 表补充 {col} 列")

        # 2. 存量回填：库存均价 = 最近一条审核通过进货的单价；领用快照 = 关联库存均价
        db.execute(text(
            "UPDATE material_stock s SET s.unit_price = ("
            "  SELECT p.cost_price FROM material_purchase p "
            "  WHERE p.farm_id = s.farm_id AND p.material_name = s.material_name "
            "    AND p.audit_status = '通过' AND p.deleted = 0 "
            "  ORDER BY p.purchase_date DESC, p.id DESC LIMIT 1"
            ") WHERE s.unit_price IS NULL"
        ))
        db.execute(text(
            "UPDATE material_consume c SET c.unit_price = ("
            "  SELECT s.unit_price FROM material_stock s WHERE s.id = c.stock_id"
            ") WHERE c.unit_price IS NULL AND c.stock_id IS NOT NULL"
        ))
        db.commit()
        print("[init] material_stock / material_consume unit_price 存量回填完成")
    except Exception as e:
        print(f"[init] unit_price 迁移跳过（非 MySQL 或已迁移）：{e}")
        db.rollback()


def _ensure_sys_notice_farm_id(db):
    """
    v1.30 通知公告多租户隔离：为老库 sys_notice 补充 farm_id 列（新库由 create_all 自动建列）。
    存量公告归类到首个养殖场，避免成为孤儿数据不可见。
    """
    from sqlalchemy import text
    try:
        rows = db.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME='sys_notice' AND COLUMN_NAME='farm_id'"
        )).fetchall()
        if not rows:
            db.execute(text("ALTER TABLE sys_notice ADD COLUMN farm_id INT"))
            # 回填：把存量公告归到第一个养殖场
            db.execute(text(
                "UPDATE sys_notice SET farm_id = "
                "(SELECT id FROM farm ORDER BY id LIMIT 1) WHERE farm_id IS NULL"
            ))
            db.execute(text("ALTER TABLE sys_notice MODIFY farm_id INT NOT NULL DEFAULT 0"))
            db.commit()
            print("[init] 已为 sys_notice 表补充 farm_id 列并回填存量公告")
    except Exception as e:
        print(f"[init] sys_notice.farm_id 迁移跳过（非 MySQL 或已迁移）：{e}")
        db.rollback()


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
        _ensure_stock_unit_price(db)
        _ensure_sys_notice_farm_id(db)
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
                # 中文操作名：遍历 app.routes 按 path+method 匹配到具体路由，取它的 OpenAPI summary
                # （如「个体入栏」「审核疫苗记录」）；匹配不到则退回原始 URL，让日志可读且不丢信息。
                # 写接口低频，逐条匹配 100+ 路由开销可忽略。
                oper_title = path
                try:
                    from starlette.routing import Match
                    scope = request.scope
                    for rr in app.routes:
                        if getattr(rr, "summary", None) and rr.matches(scope)[0] == Match.FULL:
                            oper_title = rr.summary
                            break
                except Exception:
                    pass
                record_oper_log(
                    db,
                    title=oper_title,
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
# allow_origin_regex：开发期本机 Vite dev server 端口不固定（5173 被占用会自动递增到 5174 等），
# 用正则放行 localhost/127.0.0.1 任意端口，避免第二实例（用户端）预检请求 400
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
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
