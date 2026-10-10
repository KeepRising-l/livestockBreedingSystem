"""
配置模块

使用 pydantic-settings 自动从 .env 文件读取配置，
在代码里通过 `from app.config import settings` 即可全局访问。
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，字段名与 .env 文件中的变量名一一对应"""

    # 让 pydantic 从 .env 文件读取，且环境变量名大小写不敏感
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # ===== 应用 =====
    APP_NAME: str = "智能养殖信息管理系统"
    APP_ENV: str = "dev"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ===== 数据库 =====
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "livestock_db"
    # 是否把 SQLAlchemy 执行的每条 SQL 打到控制台（调试用），默认关闭。
    # 之前是 APP_ENV == "dev" 就无条件全量打印：日志刷屏，且 Windows 终端输出本身很慢，
    # 请求里 SQL 一多体感就"卡"。需要看 SQL 时在 .env 里设 DB_ECHO=true。
    DB_ECHO: bool = False

    # ===== Redis =====
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # ===== JWT =====
    JWT_SECRET_KEY: str = "change-this-to-a-random-string-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ===== CORS =====
    # 额外放行的跨域来源（逗号分隔完整 origin，如 https://farm.example.com）；
    # 留空则仅放行本机开发端口（localhost/127.0.0.1 任意端口）
    CORS_ORIGINS: str = ""

    # ===== 超级管理员 =====
    SUPER_ADMIN_USERNAME: str = "admin"
    SUPER_ADMIN_PASSWORD: str = "admin123"
    SUPER_ADMIN_PHONE: str = "13800000000"

    @property
    def db_url(self) -> str:
        """拼接 SQLAlchemy 用的 MySQL 连接字符串"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        """拼接 Redis 连接字符串"""
        pwd = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{pwd}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    """单例模式，整个应用只读取一次 .env"""
    return Settings()


# 全局配置对象，其它模块直接 import 使用
settings = get_settings()

# 安全兜底：JWT 密钥仍是公开占位串时拒绝启动（占位串随 .env.example 公开分发，
# 知道它即可伪造任意用户 token）
_DEFAULT_JWT_SECRET = "change-this-to-a-random-string-at-least-32-chars"
if settings.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET_KEY 仍是默认占位串，拒绝启动。"
        "请在 .env 中设置随机密钥，生成方式：python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
