"""全局配置(通过 pydantic-settings 从环境变量 / .env 读取)。"""
from functools import lru_cache
from typing import Annotated, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- 应用 ----
    app_name: str = "yinyu"
    app_env: str = "dev"
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[List[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ---- 数据库 ----
    database_url: str
    database_url_sync: str

    # ---- Redis ----
    redis_url: str = "redis://127.0.0.1:6379/0"

    # ---- JWT ----
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # ---- 文件存储 ----
    upload_dir: str = "/data/uploads"
    upload_url_prefix: str = "/uploads"
    allowed_mimes: Annotated[List[str], NoDecode] = [
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-m4a",
        "video/mp4",
    ]
    max_upload_mb: int = 50

    # ---- 树洞暗号安全 ----
    treehole_max_attempts: int = 10
    treehole_attempt_window_seconds: int = 60
    treehole_lock_seconds: int = 1800

    # ---- 初始超管 ----
    superadmin_username: str = "admin"
    superadmin_password: str = "change-me"

    @field_validator("cors_origins", "allowed_mimes", mode="before")
    @classmethod
    def _split_comma(cls, v):
        if isinstance(v, str):
            # 允许 "*"
            return ["*"] if v.strip() == "*" else [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
