"""通用滑动窗口限流(Redis)。

抽自树洞解锁限流的思路,供鉴权链路(login/register/refresh/改密)等
防爆破 / 防滥用场景复用。key 由调用方决定维度(ip / ip+username / user_id 等)。
"""
from fastapi import Request

from app.config import settings
from app.core.exceptions import TooManyRequests
from redis.asyncio import Redis


def get_client_ip(request: Request) -> str:
    """取真实客户端 IP。

    生产经 Nginx 反代时,X-Forwarded-For 格式为 `client, proxy1, proxy2`,
    最右侧是直接连给我们的代理(可信),最左侧是原始客户端(攻击者可伪造)。
    从右向左跳过 TRUSTED_PROXIES 内的 IP,第一个非可信即真实客户端。

    若直接信任 XFF 首段,任何人都能 `curl -H 'X-Forwarded-For: 1.2.3.4'`
    绕过限流;本实现只信任由可信反代追加的 XFF。
    """
    xff = request.headers.get("x-forwarded-for", "")
    parts = [p.strip() for p in xff.split(",") if p.strip()]
    trusted = set(settings.trusted_proxies)

    # 从右向左剥可信代理。空 XFF / 全可信 → 回退 request.client.host。
    for ip in reversed(parts):
        if ip in trusted:
            continue
        return ip

    host = request.client.host if request.client else "unknown"
    return host or "unknown"


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
