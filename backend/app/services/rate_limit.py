"""通用滑动窗口限流(Redis)。

抽自树洞解锁限流的思路,供鉴权链路(login/register/refresh/改密)等
防爆破 / 防滥用场景复用。key 由调用方决定维度(ip / ip+username / user_id 等)。
"""
from fastapi import Request

from app.core.exceptions import TooManyRequests
from redis.asyncio import Redis


def get_client_ip(request: Request) -> str:
    """取真实客户端 IP。生产经 Nginx 反代,信任 X-Forwarded-For 首段。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return (request.client.host if request.client else "unknown") or "unknown"


async def sliding_limit(
    redis: Redis,
    key: str,
    *,
    max_attempts: int,
    window_seconds: int,
    lock_seconds: int = 0,
    message: str = "操作过于频繁,请稍后再试",
) -> None:
    """
    滑动窗口限流:
    - window 秒内最多 max_attempts 次
    - 超限则(可选)锁定 lock_seconds 秒,期间直接拒绝
    """
    if lock_seconds:
        lock_key = f"{key}:lock"
        if await redis.exists(lock_key):
            raise TooManyRequests(message)

    counter_key = f"{key}:cnt"
    count = await redis.incr(counter_key)
    if count == 1:
        await redis.expire(counter_key, window_seconds)

    if count > max_attempts:
        if lock_seconds:
            await redis.set(lock_key, "1", ex=lock_seconds)
        raise TooManyRequests(message)
