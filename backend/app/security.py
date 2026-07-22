"""密码哈希(pwdlib + bcrypt)与 JWT 编解码。

bcrypt 是刻意慢的同步 CPU 密集操作,放到默认线程池执行,
避免阻塞 asyncio 事件循环(一次登录/注册会卡住同时段的所有请求)。
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.config import settings

# 显式使用 bcrypt(对应 requirements 中的 pwdlib[bcrypt]),避免依赖 argon2
_pwd_hash = PasswordHash((BcryptHasher(),))

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


async def hash_password(plain: str) -> str:
    return await asyncio.to_thread(_pwd_hash.hash, plain)


async def verify_password(plain: str, hashed: str) -> bool:
    try:
        return await asyncio.to_thread(_pwd_hash.verify, plain, hashed)
    except Exception:
        return False


def _create_token(subject: str | int, expires_delta: timedelta, token_type: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id,
        timedelta(minutes=settings.access_token_expire_minutes),
        TOKEN_TYPE_ACCESS,
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id,
        timedelta(days=settings.refresh_token_expire_days),
        TOKEN_TYPE_REFRESH,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
