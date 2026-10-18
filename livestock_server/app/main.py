"""
FastAPI 应用入口

启动方式（在 livestock_server 目录下）：
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

或者直接运行本文件：
    python -m app.main
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.concurrency import run_in_threadpool

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
from app.modules.system.model import SysRole
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
    except Exception as e:
        print(f"[init] sys_role.perms 迁移跳过（非 MySQL 或已迁移）：{e}")
        db.rollback()


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


def _ensure_mating_audit_status(db):
    """
    配种记录审核：为老库 mating_record 补充 audit_status 列。

    背景：配种记录原先"提交即生效"（提交即把母畜置为妊娠），现在改为
    "提交 → 待审核 → 场主审核通过才置妊娠"（与饲喂记录一致）。
    存量记录都是已生效的数据，统一回填"通过"，避免历史记录涌进审核中心。
    """
    from sqlalchemy import text
    try:
        rows = db.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME='mating_record' AND COLUMN_NAME='audit_status'"
        )).fetchall()
        if not rows:
            db.execute(text(
                "ALTER TABLE mating_record ADD COLUMN audit_status VARCHAR(10) "
                "NOT NULL DEFAULT '待审核' COMMENT '审核状态：待审核/通过/驳回'"
            ))
            db.commit()
            print("[init] 已为 mating_record 表补充 audit_status 列")
            # 存量记录视为已生效，回填"通过"
            result = db.execute(text(
                "UPDATE mating_record SET audit_status='通过' WHERE audit_status='待审核'"
            ))
            db.commit()
            if result.rowcount:
                print(f"[init] mating_record.audit_status 存量回填为「通过」，共 {result.rowcount} 条")
    except Exception as e:
        print(f"[init] mating_record.audit_status 迁移跳过（非 MySQL 或已迁移）：{e}")


def _ensure_pen_species(db):
    """
    圈舍畜种归属：为老库 pen_info 补充 species 列并回填存量圈舍。

    背景：原先"某畜种的圈舍列表"是靠"圈里有没有该畜种的动物"反推的，
    新建的空圈舍没有任何动物 → 在三个畜种的列表里都查不到，且无法被指派归属。
    改为圈舍自身携带 species 字段。

    回填规则：取该圈舍内数量最多的畜种。
    圈内没有任何动物的圈舍保持 NULL（视为「待归属」，列表仍可见并标记，可手动指定）。
    """
    from sqlalchemy import text
    try:
        rows = db.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME='pen_info' AND COLUMN_NAME='species'"
        )).fetchall()
        if not rows:
            db.execute(text("ALTER TABLE pen_info ADD COLUMN species VARCHAR(10) NULL"))
            db.commit()
            print("[init] 已为 pen_info 表补充 species 列")

        # 存量回填：按圈内动物数量最多的畜种归属；空圈舍保持 NULL
        result = db.execute(text(
            "UPDATE pen_info p SET p.species = ("
            "  SELECT a.species FROM animal_archive a "
            "  WHERE a.pen_id = p.id AND a.deleted = 0 AND a.species IS NOT NULL "
            "  GROUP BY a.species ORDER BY COUNT(*) DESC LIMIT 1"
            ") WHERE p.species IS NULL"
        ))
        db.commit()
        if result.rowcount:
            print(f"[init] pen_info.species 存量回填完成，共 {result.rowcount} 个圈舍")

        # 补索引（create_all 不会给已存在的表加索引）
        idx = db.execute(text(
            "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS "
            "WHERE TABLE_NAME='pen_info' AND INDEX_NAME='ix_pen_info_species'"
        )).fetchall()
        if not idx:
            db.execute(text("CREATE INDEX ix_pen_info_species ON pen_info (species)"))
            db.commit()
            print("[init] 已为 pen_info.species 建索引")
    except Exception as e:
        print(f"[init] pen_info.species 迁移跳过（非 MySQL 或已迁移）：{e}")
        db.rollback()


def _ensure_vet_role_perms(db):
    """
    存量库角色权限修复：兽医角色不应包含「物资库存（inventory）」模块。

    背景：ROLE_PERMS["vet"] 早期误授了 inventory，而 init_rbac_data() 只在 sys_role
    为空时首次初始化，已有环境不会随代码更新。这里用 ORM 做一次幂等修复：
    仅当 vet.perms 中确实含 "inventory" 时才回写（兼容 MySQL 与测试用 SQLite 内存库），
    不包含则静默跳过；异常回滚，不影响应用启动。
    """
    try:
        role = db.query(SysRole).filter(SysRole.role_key == "vet").first()
        if not role or not role.perms:
            return
        try:
            perms = json.loads(role.perms)
        except (ValueError, TypeError):
            # perms 不是合法 JSON（老数据脏值），不做猜测性修改
            return
        if not isinstance(perms, list) or "inventory" not in perms:
            return
        role.perms = json.dumps([p for p in perms if p != "inventory"], ensure_ascii=False)
        db.commit()
        print("[init] 已移除兽医角色的「物资库存」权限（inventory）")
    except Exception as e:
        print(f"[init] 兽医角色权限修复跳过：{e}")
        db.rollback()


def _ensure_sale_order_no_index(db):
    """
    销售订单号唯一约束调整：order_no 由「全局唯一」改为「场内唯一」。

    背景：订单编号规则是 SO + yyyyMMdd + 场内当日流水，流水号按 farm_id 统计，
    因此不同养殖场在同一天必然生成相同编号（如两家场同时出第一单都是 SO20261018001）。
    老库上 order_no 带着全局 UNIQUE 索引，B 场出栏时直接 IntegrityError 500。
    这里把全局唯一索引降级为普通索引（保留检索能力），唯一性由业务层按 farm_id 保证。
    幂等：索引已是非唯一则跳过；非 MySQL（测试库 SQLite）走异常忽略。
    """
    from sqlalchemy import text
    try:
        rows = db.execute(text(
            "SELECT INDEX_NAME, NON_UNIQUE FROM INFORMATION_SCHEMA.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='sale_order' "
            "  AND COLUMN_NAME='order_no'"
        )).fetchall()
        if not rows:
            return
        unique_idx = [r[0] for r in rows if int(r[1]) == 0 and r[0] != "PRIMARY"]
        for name in unique_idx:
            db.execute(text(f"ALTER TABLE sale_order DROP INDEX `{name}`"))
            db.commit()
            print(f"[init] 已移除 sale_order.order_no 的全局唯一索引（{name}），改为场内唯一")
        if unique_idx and not any(int(r[1]) == 1 for r in rows):
            db.execute(text("CREATE INDEX ix_sale_order_order_no ON sale_order (order_no)"))
            db.commit()
            print("[init] 已为 sale_order.order_no 建普通索引")
    except Exception as e:
        print(f"[init] sale_order.order_no 索引迁移跳过（非 MySQL 或已迁移）：{e}")
        db.rollback()


def _ensure_pen_count_sync(db):
    """
    圈舍存栏数校准：pen_info.current_count 与「圈内在栏档案数」不一致时按实际重算。

    背景：在栏口径是 status ∈ 在栏/种用/隔离/待出栏 的未删除档案
    （与 pen/animal/health/statistics/scheduler 各处列表口径一致）。
    历史上有两条路径会让计数漂移：
      1) 档案编辑里把状态改成「已出栏/死亡」，但当时没有联动扣减圈舍存栏；
      2) 早期演示/导入数据直接写库。
    计数漂移会连锁影响：圈舍显示存栏虚高 → 自动分配找不到空位、容量校验误报已满。
    这里按实际档案数一次性校准（幂等），并打印被修正的圈舍，便于追查来源。
    """
    from sqlalchemy import text
    try:
        rows = db.execute(text(
            "SELECT p.id, p.pen_code, p.current_count, "
            "  (SELECT COUNT(*) FROM animal_archive a WHERE a.pen_id = p.id "
            "     AND a.deleted = 0 AND a.status IN ('在栏','种用','隔离','待出栏')) "
            "FROM pen_info p WHERE p.deleted = 0"
        )).fetchall()
        fixed = []
        for pen_id, pen_code, current, actual in rows:
            if int(current or 0) == int(actual or 0):
                continue
            db.execute(
                text("UPDATE pen_info SET current_count = :n WHERE id = :id"),
                {"n": int(actual or 0), "id": pen_id},
            )
            fixed.append(f"{pen_code}({current}->{actual})")
        if fixed:
            db.commit()
            print(f"[init] 圈舍存栏数已按实际档案校准：{'、'.join(fixed)}")
    except Exception as e:
        print(f"[init] 圈舍存栏数校准跳过：{e}")
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
        _ensure_pen_species(db)
        _ensure_mating_audit_status(db)
        _ensure_sale_order_no_index(db)
        _ensure_pen_count_sync(db)
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
            print(f"[init] 已创建超级管理员：{settings.SUPER_ADMIN_USERNAME}（密码取自配置项 SUPER_ADMIN_PASSWORD，不回显）")

        # 初始化字典数据（首次启动时）
        init_dict_data(db)
        # 初始化 RBAC 角色 + 菜单（首次启动时）
        init_rbac_data(db)
        # 存量库修复：兽医角色不应包含「物资库存」模块（幂等，首次初始化后也能生效）
        _ensure_vet_role_perms(db)
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


def _resolve_oper_title(request: Request) -> str:
    """按 path+method 匹配具体路由，取 OpenAPI summary 作为中文操作名；匹配不到退回原始 URL"""
    try:
        from starlette.routing import Match
        scope = request.scope
        for rr in app.routes:
            if getattr(rr, "summary", None) and rr.matches(scope)[0] == Match.FULL:
                return rr.summary
    except Exception:
        pass
    return request.url.path


def _write_oper_log(request: Request, method: str, user_id: int, status: int, error_msg: str | None) -> None:
    """oper_log 落库（同步，供线程池调用）：查用户名 + 写库"""
    db = SessionLocal()
    try:
        user_name = None
        u = db.query(User).filter(User.id == user_id).first()
        user_name = u.username if u else None
        record_oper_log(
            db,
            title=_resolve_oper_title(request),
            business_type={"POST": "add", "PUT": "update", "DELETE": "delete"}.get(method, "other"),
            method=method,
            oper_url=request.url.path,
            oper_user_id=user_id,
            oper_name=user_name,
            oper_ip=request.client.host if request.client else None,
            status=status,
            error_msg=error_msg,
        )
    finally:
        db.close()


@app.middleware("http")
async def oper_log_middleware(request: Request, call_next):
    """操作日志中间件：记录 POST/PUT/DELETE 写请求到 oper_log 表"""
    method = request.method
    path = request.url.path
    if method not in ("POST", "PUT", "DELETE") or not path.startswith("/api/"):
        return await call_next(request)

    # 从 token 解析当前用户
    user_id = None
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

    # 缓存响应体后再回放：BaseHTTPMiddleware 的流式响应没有 .body 属性（原实现恒取到 None，
    # 导致所有操作日志一律记成功），必须显式读出才能判断业务 code
    body_bytes = b""
    async for chunk in response.body_iterator:
        if isinstance(chunk, str):
            body_bytes += chunk.encode("utf-8")
        else:
            body_bytes += chunk

    status, error_msg = 1, None
    try:
        data = json.loads(body_bytes)
        if data.get("code", 200) != 200:
            status = 0
            error_msg = str(data.get("msg", ""))[:200]
    except Exception:
        pass

    if user_id is not None:
        # 同步 DB 操作放入线程池，避免阻塞事件循环
        try:
            await run_in_threadpool(_write_oper_log, request, method, user_id, status, error_msg)
        except Exception:
            logger.warning(f"oper_log 落库失败 {method} {path}")

    # 用缓存的响应体重建返回体（header 透传，保持 CORS 等语义）
    return Response(
        content=body_bytes,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )

# CORS 跨域配置
# allow_origin_regex：开发期本机 Vite dev server 端口不固定（5173 被占用会自动递增到 5174 等），
# 用正则放行 localhost/127.0.0.1 任意端口，避免第二实例（用户端）预检请求 400。
# 生产部署通过 .env 的 CORS_ORIGINS 追加正式域名（逗号分隔）。
_cors_extra = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", *_cors_extra],
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
