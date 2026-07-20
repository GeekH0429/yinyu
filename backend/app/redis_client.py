"""Redis 异步连接(用于缓存、限流、token 黑名单等)。"""
from redis.asyncio import Redis, from_url

from app.config import settings

redis: Redis = from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> Redis:
    return redis
