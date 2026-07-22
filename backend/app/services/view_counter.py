"""浏览计数:Redis 累积 + 日级去重,后台定时批量回写 DB。

避免每次访问详情都触发 UPDATE + commit(热行写争用、作者预览也计数、刷新无去重)。
同一 viewer 当天对同一对象只计一次;增量先存 Redis,由后台任务批量落库。
"""
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.treehole import TreeHole

_KIND_MODEL = {"article": Article, "treehole": TreeHole}


async def incr_view(redis: Redis, kind: str, item_id: int, viewer: str) -> None:
    """记一次浏览。同一 viewer 当天对同一对象只计一次。"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    dedup = await redis.set(
        f"view:dedup:{kind}:{item_id}:{viewer}:{today}", "1", nx=True, ex=90000
    )
    if not dedup:
        return  # 今日已计
    await redis.incr(f"view:cnt:{kind}:{item_id}")


async def flush_pending(redis: Redis, db: AsyncSession) -> None:
    """把 Redis 中累积的浏览增量批量回写 DB,然后清零。"""
    deltas: dict[str, dict[int, int]] = {k: {} for k in _KIND_MODEL}
    async for key in redis.scan_iter(match="view:cnt:*", count=500):
        parts = key.split(":")
        if len(parts) != 4:
            continue
        _, _, kind, item_id_str = parts
        if kind not in _KIND_MODEL:
            continue
        val = await redis.getdel(key)
        if not val:
            continue
        item_id = int(item_id_str)
        deltas[kind][item_id] = deltas[kind].get(item_id, 0) + int(val)

    for kind, items in deltas.items():
        model = _KIND_MODEL[kind]
        for item_id, delta in items.items():
            await db.execute(
                update(model)
                .where(model.id == item_id)
                .values(view_count=model.view_count + delta)
                .execution_options(synchronize_session=False)
            )
    if any(items for items in deltas.values()):
        await db.commit()
