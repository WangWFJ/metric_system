# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List
import secrets, json

class Settings(BaseSettings):
    PROJECT_NAME: str = "data_proj_v1"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "mysql+aiomysql://wangfanjun:01020304@10.101.192.2:3306/db_indicator?charset=utf8mb4"

    # 每个 worker 连接池大小
    DB_POOL_SIZE: int = 4
    DB_MAX_OVERFLOW: int = 4
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    PANDAS_THREAD_WORKERS: int = 4
    PANDAS_JOB_CONCURRENCY: int = 4

    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ✅ 以「字符串」读取，避免 DotEnv 对复杂类型做 JSON 解析
    # 允许三种写法：
    #   1) "*" 
    #   2) 逗号分隔：https://a.com,https://b.com
    #   3) JSON 数组：["https://a.com","https://b.com"]
    CORS_ALLOW_ORIGINS: str = "*"

    DEBUG: bool = True  # 开发环境 True，生产改 False

    # 同时尝试根目录与 app 目录
    _repo_root = Path(__file__).resolve().parents[2]
    _app_dir = Path(__file__).resolve().parents[1]
    model_config = SettingsConfigDict(
        env_file=[
            str(_repo_root / ".env"),
            str(_app_dir / ".env"),
        ],
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        s = (self.CORS_ALLOW_ORIGINS or "").strip()
        if not s or s == "*":
            return ["*"]
        if s.startswith("["):
            try:
                arr = json.loads(s)
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                pass
        # 默认当作逗号分隔
        return [seg.strip() for seg in s.split(",") if seg.strip()]

settings = Settings()
