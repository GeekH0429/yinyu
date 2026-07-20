"""树洞暗号:生成、唯一性校验、自定义;以及暗号解锁的限流(防 6 位爆破)。"""
import secrets

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import Conflict, TooManyRequests
from app.models.treehole import CODE_LENGTH, TreeHole


def generate_code() -> str:
    """随机 CODE_LENGTH 位数字(前导零补齐)。"""
    return f"{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}"


async def is_code_taken(db: AsyncSession, code: str, exclude_id: int | None = None) -> bool:
    stmt = select(TreeHole.id).where(TreeHole.code == code)
    if exclude_id is not None:
        stmt = stmt.where(TreeHole.id != exclude_id)
    return await db.scalar(stmt) is not None


async def allocate_code(
    db: AsyncSession, preferred: str | None = None, exclude_id: int | None = None
) -> str:
    """
    分配一个全局唯一的 6 位暗号。
    - preferred 非空:校验唯一性后使用(自定义暗号)
    - preferred 为空:随机生成并重试至唯一(刷新)
    """
    if preferred:
        if await is_code_taken(db, preferred, exclude_id):
            raise Conflict("该暗号已被占用,换一个吧")
        return preferred

    for _ in range(30):
        candidate = generate_code()
        if not await is_code_taken(db, candidate, exclude_id):
            return candidate
    raise Conflict("暗号生成失败,请稍后重试")


async def assert_unlock_allowed(redis: Redis, client_ip: str) -> None:
    """
    暗号解锁的滑动窗口限流:
    - window 秒内最多 max_attempts 次尝试(无论对错,防止枚举)
    - 超限则锁定 lock_seconds 秒
    """
    lock_key = f"th:lock:{client_ip}"
    if await redis.exists(lock_key):
        raise TooManyRequests("尝试次数过多,已锁定,请稍后再试")

    counter_key = f"th:att:{client_ip}"
    count = await redis.incr(counter_key)
    if count == 1:
        await redis.expire(counter_key, settings.treehole_attempt_window_seconds)

    if count > settings.treehole_max_attempts:
        await redis.set(lock_key, "1", ex=settings.treehole_lock_seconds)
        raise TooManyRequests("尝试次数过多,已锁定,请稍后再试")
