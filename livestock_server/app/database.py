"""
数据库连接模块

- engine：数据库引擎，整个应用共用一个
- SessionLocal：会话工厂，每次请求创建一个独立会话
- Base：所有 ORM 模型的基类
- get_db：FastAPI 依赖，用于在请求中获取数据库会话并自动关闭
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

# 创建数据库引擎
# pool_pre_ping=True：每次取连接前先 ping 一下，避免连接断开导致报错
# pool_recycle=3600：连接回收时间（秒），避免 MySQL 默认 8 小时空闲断开
engine = create_engine(
    settings.db_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=settings.DB_ECHO,  # 需要观察 SQL 时在 .env 里把 DB_ECHO 设为 true
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 模型基类
Base = declarative_base()


def get_db():
    """
    FastAPI 依赖函数：在请求开始时创建一个数据库会话，请求结束后关闭。

    使用方式：
        @router.get("/xxx")
        def xxx(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
