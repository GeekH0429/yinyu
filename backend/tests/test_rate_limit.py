"""通用滑动窗口限流测试。"""
import pytest

from app.core.exceptions import TooManyRequests
from app.services.rate_limit import sliding_limit


async def test_sliding_limit_first_call_sets_expire(fake_redis):
    key = "rl:svc1"
    await sliding_limit(fake_redis, key, max_attempts=5, window_seconds=60)
    ttl = await fake_redis.ttl(f"{key}:cnt")
    assert 0 < ttl <= 60, "首次 incr 后应设置 expire"


async def test_sliding_limit_lock_set_when_exceed(fake_redis):
    key = "rl:svc2"
    # 用 lock_seconds 触发 lock 写入路径
    for _ in range(3):
        await sliding_limit(fake_redis, key, max_attempts=3, window_seconds=60, lock_seconds=30)

    with pytest.raises(TooManyRequests):
        await sliding_limit(fake_redis, key, max_attempts=3, window_seconds=60, lock_seconds=30)

    assert await fake_redis.exists(f"{key}:lock"), "超限且 lock_seconds>0 时应写 lock key"


async def test_sliding_limit_no_lock_when_lock_seconds_zero(fake_redis):
    """lock_seconds=0 时超限只拒绝,不写 lock。"""
    key = "rl:svc3"
    for _ in range(2):
        await sliding_limit(fake_redis, key, max_attempts=2, window_seconds=60, lock_seconds=0)

    with pytest.raises(TooManyRequests):
        await sliding_limit(fake_redis, key, max_attempts=2, window_seconds=60, lock_seconds=0)

    assert not await fake_redis.exists(f"{key}:lock"), "lock_seconds=0 时不应写 lock key"
