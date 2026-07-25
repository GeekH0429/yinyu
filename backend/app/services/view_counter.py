"""浏览计数:Redis 累积 + 日级去重,后台定时批量回写 DB。

避免每次访问详情都触发 UPDATE + commit(热行写争用、作者预览也计数、刷新无去重)。
同一 viewer 当天对同一对象只计一次;增量先存 Redis,由后台任务批量落库。

三层计数:
- 总量 view:cnt:{kind}:{item_id}       —— flusher 30s 回写 DB(Article.view_count)
- 按日 view:daily:{kind}:{YYYYMMDD}    —— archiver 每日凌晨归档到 article_daily_views
- 去重 view:dedup:...                   —— 25h TTL,同 viewer 当天同对象只算一次

Redis 是缓冲,DB 是真理之源。Redis 全炸也只丢"今天还没归档"的按日数据,
趋势曲线不影响(已归档的在 DB),总量不影响(独立链路)。
"""
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_daily_view import ArticleDailyView
from app.models.treehole import TreeHole

# 北京时区:与 stats._parse_date_range 对齐,避免 UTC vs CN 切日错位 8 小时
CN_TZ = timezone(timedelta(hours=8))

_KIND_MODEL = {"article": Article, "treehole": TreeHole}

# dirty set:有计数变更的 (kind, item_id) 集合。flusher 用 SMEMBERS 精准取,
# 替代早期 SCAN 全库扫描(O(N) 随业务增长)。
_DIRTY_KEY = "view:dirty"

# 按日计数 key 模板:view:daily:{kind}:{YYYYMMDD}
# TTL 8 天:覆盖 archiver 8 次容错(每天凌晨跑一次,GETDEL 后删除;
# 万一某次跑挂,8 天内补跑仍能拿到原值,过期前最后一道兜底)。
_DAILY_TTL = 8 * 24 * 3600

# 归档窗口:每天凌晨扫"昨天到 N 天前"的所有按日 key,GETDEL 后写 DB。
# 8 天窗口与 _DAILY_TTL 对齐,确保 TTL 过期前一定被扫到。
_ARCHIVE_WINDOW_DAYS = 8


async def incr_view(redis: Redis, kind: str, item_id: int, viewer: str) -> None:
    """记一次浏览。同一 viewer 当天对同一对象只计一次。

    同时维护两个计数:
    - view:cnt:{kind}:{item_id}     总累计(由 flusher 回写 DB)
    - view:daily:{kind}:{YYYYMMDD}  当日计数(由 archiver 归档到 DB)
    """
    today = datetime.now(CN_TZ).strftime("%Y%m%d")
    dedup = await redis.set(
        f"view:dedup:{kind}:{item_id}:{viewer}:{today}", "1", nx=True, ex=90000
    )
    if not dedup:
        return  # 今日已计
    # pipeline:累加总量 + 标记 dirty + 累加当日(给趋势曲线读)
    daily_key = f"view:daily:{kind}:{today}"
    pipe = redis.pipeline()
    pipe.incr(f"view:cnt:{kind}:{item_id}")
    pipe.sadd(_DIRTY_KEY, f"{kind}:{item_id}")
    pipe.incr(daily_key)
    pipe.expire(daily_key, _DAILY_TTL)
    await pipe.execute()


async def flush_pending(redis: Redis, db: AsyncSession) -> None:
    """把 Redis 中累积的浏览增量批量回写 DB,然后清零。"""
    members = await redis.smembers(_DIRTY_KEY)
    if not members:
        return
    # 只移除本次取到的成员;期间新 sadd 的成员留给下一轮(不会丢计数)。
    await redis.srem(_DIRTY_KEY, *members)

    deltas: dict[str, dict[int, int]] = {k: {} for k in _KIND_MODEL}
    for member in members:
        if isinstance(member, bytes):
            member = member.decode("utf-8", "ignore")
        kind, _, item_id_str = member.partition(":")
        if kind not in _KIND_MODEL or not item_id_str.isdigit():
            continue
        val = await redis.getdel(f"view:cnt:{kind}:{item_id_str}")
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


async def archive_daily_views(redis: Redis, db: AsyncSession) -> int:
    """把 Redis 按日浏览量归档到 article_daily_views 表。

    每天凌晨由 `_daily_archiver` 调用。扫"昨天到 N 天前"的
    `view:daily:article:{YYYYMMDD}` key,GETDEL 原子取值后 UPSERT 到 DB。

    GETDEL 保证每个 key 至多被处理一次(幂等);UPSERT 用累加语义,
    即便同一 key 被分批归档(凌晨 + 补跑)也不会丢/翻倍。

    Returns: 本次实际归档的(日期, 增量)条数。
    """
    today_cn = datetime.now(CN_TZ).date()
    rows = 0
    for offset in range(1, _ARCHIVE_WINDOW_DAYS + 1):
        target = today_cn - timedelta(days=offset)
        key = f"view:daily:article:{target.strftime('%Y%m%d')}"
        val = await redis.getdel(key)
        if not val:
            continue
        delta = int(val)
        if delta <= 0:
            continue
        # ON CONFLICT (date) DO UPDATE SET count = count + delta
        # 累加:同一天可能被多次归档(凌晨跑过 + 补跑),累加不重复。
        stmt = (
            pg_insert(ArticleDailyView)
            .values(date=target, count=delta)
            .on_conflict_do_update(
                index_elements=[ArticleDailyView.date],
                set_={"count": ArticleDailyView.count + delta},
            )
            .execution_options(synchronize_session=False)
        )
        await db.execute(stmt)
        rows += 1
    if rows:
        await db.commit()
    return rows

