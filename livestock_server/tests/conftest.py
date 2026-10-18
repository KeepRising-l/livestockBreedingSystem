"""
pytest 公共夹具：SQLite 内存库 + TestClient。

设计要点（对应《智能养殖项目改进指引》P1-D）：
- 测试全程使用 SQLite 内存库（StaticPool 共享单连接），不连接开发/生产 MySQL；
  app.database.engine 虽按 .env 创建，但从未被使用（依赖覆盖 + 不触发 lifespan）。
- TestClient 不用 with 上下文 → 不执行 lifespan → 不跑 init_db()（create_all 直连
  生产引擎）也不启动 APScheduler。
- 操作日志中间件直接引用 app.main.SessionLocal，统一替换为测试会话工厂，
  避免 POST/PUT/DELETE 请求把 oper_log 写进开发/生产库。
- 每个用例前 drop_all + create_all + 重建超管，用例间互不影响、可重复执行。

运行（livestock_server 目录下）：
    python -m pytest tests/ -v
"""
import os

# 必须在 import app 之前设置：全新环境没有 .env 时也能保证 JWT 密钥可用
# （环境变量优先级高于 .env，不会覆盖已有配置）
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "pytest-only-secret-key-0123456789abcdef0123456789abcdef",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.models  # noqa: F401  触发所有模型注册，保证建表完整
import app.main as app_main
from app.main import app as fastapi_app
from app.core.security import hash_password
from app.models.user import User

# ===== 测试专用 SQLite 内存引擎（所有连接共享同一内存库） =====
engine = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 依赖覆盖：请求中的 get_db 全部走 SQLite 内存库
fastapi_app.dependency_overrides[get_db] = override_get_db
# 操作日志中间件直接引用 app.main.SessionLocal（不走依赖注入），单独替换
app_main.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def clean_db():
    """每个用例前重建全部表 + 超管账号，保证用例独立、可重复执行"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        db.add(User(
            username="admin",
            password=hash_password("admin123"),
            real_name="超级管理员",
            phone="13800000000",
            user_type=1,
            status=1,
        ))
        db.commit()
    yield


@pytest.fixture
def client():
    """FastAPI 测试客户端（不走 lifespan，不触发 init_db / 定时任务）"""
    return TestClient(fastapi_app)


# ===== 测试辅助 =====

def login(client: TestClient, username: str, password: str) -> dict:
    """登录并返回带 Authorization 的请求头"""
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    body = r.json()
    assert body["code"] == 200, f"登录失败：{body}"
    return {"Authorization": f"Bearer {body['data']['access_token']}"}


def register_farm(client: TestClient, farm_name: str, username: str) -> dict:
    """注册一个养殖场主（自动建场），返回请求头"""
    r = client.post("/api/v1/auth/register/owner", json={
        "farm_name": farm_name,
        "username": username,
        "password": "123456",
        "real_name": f"{username}-实名",
        "phone": "13900000001",
        "livestock_types": "牛",
    })
    body = r.json()
    assert body["code"] == 200, f"注册失败：{body}"
    return login(client, username, "123456")


def get_farm_id(client: TestClient, admin_headers: dict, farm_name: str) -> int:
    """超管查询指定名称养殖场的 ID"""
    r = client.get("/api/v1/farm/list", headers=admin_headers)
    for f in r.json()["data"]:
        if f["farm_name"] == farm_name:
            return f["id"]
    raise AssertionError(f"养殖场 {farm_name} 不存在")
