"""树洞暗号相关纯逻辑测试。"""
import pytest

from app.config import settings
from app.core.exceptions import TooManyRequests
from app.services.treehole_code import assert_unlock_allowed, generate_code


def test_generate_code_length_and_digits():
    code = generate_code()
    assert len(code) == 6
    assert code.isdigit(), f"暗号必须纯数字,得到 {code!r}"


def test_generate_code_can_have_leading_zeros():
    """6 位空间小,采样 500 次应能见到前导零。"""
    codes = [generate_code() for _ in range(500)]
    assert any(c.startswith("0") for c in codes), "应能生成前导零的暗号"


async def test_assert_unlock_allowed_locks_after_threshold(fake_redis):
    ip = "1.2.3.4"
    # 前 max_attempts 次放行
    for _ in range(settings.treehole_max_attempts):
        await assert_unlock_allowed(fake_redis, ip)

    # 第 max_attempts + 1 次抛 TooManyRequests 并设置 lock key
    with pytest.raises(TooManyRequests):
        await assert_unlock_allowed(fake_redis, ip)
    assert await fake_redis.exists(f"th:lock:{ip}"), "超限后应写入 lock key"


async def test_assert_unlock_allowed_during_lock_period(fake_redis):
    ip = "5.6.7.8"
    # 预先写入 lock 模拟"已锁定"
    await fake_redis.set(f"th:lock:{ip}", "1", ex=60)

    # lock 期内调用不应再增加 counter(直接拒绝)
    before = await fake_redis.get(f"th:att:{ip}")
    with pytest.raises(TooManyRequests):
        await assert_unlock_allowed(fake_redis, ip)
    after = await fake_redis.get(f"th:att:{ip}")
    assert before == after, "lock 期内不应再 incr counter"
