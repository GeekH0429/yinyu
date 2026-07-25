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
    # 信任的反代 IP(逗号分隔)。get_client_ip 从 X-Forwarded-For 最右开始
    # 跳过这些 IP,第一个非可信即真实客户端。默认只信任本机回环(单 Nginx 部署)。
    trusted_proxies: Annotated[List[str], NoDecode] = ["127.0.0.1", "::1"]

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
        "audio/aac", "audio/flac", "audio/webm", "audio/ogg",
        "video/mp4",
    ]
    max_upload_mb: int = 50

    # ---- 树洞暗号安全 ----
    treehole_max_attempts: int = 10
    treehole_attempt_window_seconds: int = 60
    treehole_lock_seconds: int = 1800
    # 树洞换暗号限流(防止自动化刷占暗号空间)
    treehole_change_code_max_attempts: int = 10
    treehole_change_code_window_seconds: int = 60
    treehole_change_code_lock_seconds: int = 60

    # ---- 评论限流 ----
    comment_max_attempts: int = 5
    comment_attempt_window_seconds: int = 60
    comment_lock_seconds: int = 300

    # ---- 暖话 ----
    warm_words_daily_limit: int = 30  # 每用户每日随机抽取次数上限(自然日)
    warm_words_scene_window_seconds: int = 86400  # 限流窗口(实际 key 带日期,设 2 天保险过期)

    # ---- 邮件通知 (SMTP) ----
    # 总开关:False 时邮件模块整体 no-op(不连接 SMTP,只记日志)。
    # 用 SSL(默认 465)时 smtp_use_tls=True;用 STARTTLS(587)时 smtp_use_tls=False。
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""              # 发件人地址,如 noreply@example.com
    smtp_use_tls: bool = True        # True=SSL; False=STARTTLS
    # 邮件中显示的产品名 / 站点名
    smtp_sender_name: str = "yinyu"

    # ---- 统计缓存 ----
    stats_cache_ttl_seconds: int = 300

    # ---- 初始超管 ----
    superadmin_username: str = "admin"
    superadmin_password: str = "change-me"

    @field_validator("cors_origins", "allowed_mimes", "trusted_proxies", mode="before")
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
