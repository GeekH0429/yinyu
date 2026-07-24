"""统计数据路由。"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Type, TypeVar

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.articles import STATUS_PUBLISHED
from app.config import settings
from app.database import get_db
from app.deps import require_admin
from app.models.article import Article
from app.models.media import Media
from app.models.treehole import TreeHole
from app.models.user import User
from app.redis_client import get_redis
from app.schemas.stats import (
    ActiveUserItem,
    ContentRankItem,
    OverviewOut,
    TrendOut,
    TrendPoint,
)

router = APIRouter(
    prefix="/stats",
    tags=["统计数据"],
    dependencies=[Depends(require_admin)],
)

logger = logging.getLogger("yinyu.stats")

# 北京时区
CN_TZ = timezone(timedelta(hours=8))

StatsRange = str  # Literal["7d", "30d", "90d"]

# 时间范围 → 天数(模块级常量,避免每个 handler 重复定义)
_DAYS = {"7d": 7, "30d": 30, "90d": 90}

# 趋势/排行缓存 TTL(秒)。overview 用 stats_cache_ttl_seconds(默认 300s),
# 这些聚合更重且对实时性要求更低,给短一些避免缓存与 DB 漂移过大。
_TRENDS_CACHE_TTL = 60
_RANK_CACHE_TTL = 60

_T = TypeVar("_T", bound=BaseModel)


def _parse_date_range(days: int) -> tuple[datetime, datetime]:
    """生成时间范围(北京时间)。"""
    now = datetime.now(CN_TZ)
    start = now - timedelta(days=days)
    # 转为 UTC 用于数据库查询
    start_utc = start.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    now_utc = now.astimezone(timezone.utc)
    return start_utc, now_utc


async def _cache_get_or_set(
    redis,
    cache_key: str,
    loader: Callable[[], Awaitable[_T]],
    model: Type[_T],
    ttl: int,
) -> _T:
    """缓存读穿:命中则反序列化返回;未命中跑 loader、写缓存后返回。

    Redis 异常一律降级到 DB(不让缓存挂掉统计接口)。
    """
    try:
        cached = await redis.get(cache_key)
        if cached:
            return model.model_validate_json(cached)
    except Exception:  # noqa: BLE001
        logger.warning("stats cache read failed, fallback to DB", exc_info=True)

    out = await loader()
    try:
        await redis.set(cache_key, out.model_dump_json(), ex=ttl)
    except Exception:  # noqa: BLE001
        logger.warning("stats cache write failed", exc_info=True)
    return out


async def _fetch_overview(db: AsyncSession, range_key: str) -> OverviewOut:
    """从 DB 查询 overview(4 次聚合查询)。"""
    days = _DAYS.get(range_key, 30)
    start_utc, _now_utc = _parse_date_range(days)

    # articles:总数 + 已发布 + 时间范围内新增 + 累计 view/like(合并为单查询)
    art_row = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Article.status == STATUS_PUBLISHED).label("published"),
            func.count().filter(Article.created_at >= start_utc).label("new"),
            func.coalesce(func.sum(Article.view_count), 0).label("views"),
            func.coalesce(func.sum(Article.like_count), 0).label("likes"),
        ).select_from(Article)
    )
    art = art_row.one()
    total_articles = art.total or 0
    total_published = art.published or 0
    new_articles = art.new or 0
    total_views = int(art.views or 0)
    total_likes = int(art.likes or 0)

    # users:总数 + 时间范围内新增
    user_row = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(User.created_at >= start_utc).label("new"),
        ).select_from(User)
    )
    u = user_row.one()
    total_users = u.total or 0
    new_users = u.new or 0

    # treeholes:总数 + 时间范围内新增
    th_row = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(TreeHole.created_at >= start_utc).label("new"),
        ).select_from(TreeHole)
    )
    t = th_row.one()
    total_treeholes = t.total or 0
    new_treeholes = t.new or 0

    # media:总数 + 存储字节
    media_row = await db.execute(
        select(
            func.count().label("total"),
            func.coalesce(func.sum(Media.size_bytes), 0).label("bytes"),
        ).select_from(Media)
    )
    m = media_row.one()
    total_media = m.total or 0
    total_storage = int(m.bytes or 0)

    return OverviewOut(
        total_users=total_users,
        total_articles=total_articles,
        total_published=total_published,
        total_treeholes=total_treeholes,
        total_media=total_media,
        new_users=new_users,
        new_articles=new_articles,
        new_treeholes=new_treeholes,
        total_views=total_views,
        total_likes=total_likes,
        total_storage_bytes=total_storage,
    )


@router.get("/overview", response_model=OverviewOut)
async def get_overview(
    range: StatsRange = Query("30d", description="时间范围"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """总体概览:用户数/文章数/树洞数等关键指标。

    Redis 缓存(TTL 由 `stats_cache_ttl_seconds` 控制,默认 300s)。
    缓存 key 必须带 range 维度,否则 7d/30d/90d 会串数据。
    Redis 不可用时回退 DB。
    """
    return await _cache_get_or_set(
        redis,
        f"stats:overview:{range}",
        lambda: _fetch_overview(db, range),
        OverviewOut,
        settings.stats_cache_ttl_seconds,
    )


@router.get("/trends", response_model=TrendOut)
async def get_trends(
    range: StatsRange = Query("30d", description="时间范围"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """用户增长与内容发布趋势(按日期分组,Redis 缓存 60s)。"""
    async def _load() -> TrendOut:
        days = _DAYS.get(range, 30)
        start_utc, _now_utc = _parse_date_range(days)

        # 用户增长趋势
        user_trend = await db.execute(
            select(
                cast(User.created_at, Date).label("date"),
                func.count(User.id).label("count"),
            )
            .where(User.created_at >= start_utc)
            .group_by(cast(User.created_at, Date))
            .order_by("date")
        )
        user_points = [
            TrendPoint(date=str(r.date), count=r.count) for r in user_trend.all()
        ]

        # 文章发布趋势
        article_trend = await db.execute(
            select(
                cast(Article.created_at, Date).label("date"),
                func.count(Article.id).label("count"),
            )
            .where(Article.created_at >= start_utc)
            .group_by(cast(Article.created_at, Date))
            .order_by("date")
        )
        article_points = [
            TrendPoint(date=str(r.date), count=r.count) for r in article_trend.all()
        ]

        # 树洞发布趋势
        treehole_trend = await db.execute(
            select(
                cast(TreeHole.created_at, Date).label("date"),
                func.count(TreeHole.id).label("count"),
            )
            .where(TreeHole.created_at >= start_utc)
            .group_by(cast(TreeHole.created_at, Date))
            .order_by("date")
        )
        treehole_points = [
            TrendPoint(date=str(r.date), count=r.count) for r in treehole_trend.all()
        ]

        return TrendOut(
            users=user_points,
            articles=article_points,
            treeholes=treehole_points,
        )

    return await _cache_get_or_set(
        redis,
        f"stats:trends:{range}",
        _load,
        TrendOut,
        _TRENDS_CACHE_TTL,
    )


@router.get("/top-articles", response_model=list[ContentRankItem])
async def get_top_articles(
    range: StatsRange = Query("30d", description="时间范围"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """热门文章排行(按点赞数,Redis 缓存 60s)。"""
    cache_key = f"stats:topArticles:{range}:{limit}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            return [ContentRankItem.model_validate(item) for item in json.loads(cached)]
    except Exception:  # noqa: BLE001
        logger.warning("stats top-articles cache read failed, fallback to DB", exc_info=True)

    days = _DAYS.get(range, 30)
    start_utc, _now_utc = _parse_date_range(days)

    rows = await db.execute(
        select(
            Article.id,
            Article.title,
            Article.like_count,
            Article.view_count,
            Article.published_at,
            User.nickname.label("author_name"),
        )
        .join(User, User.id == Article.author_id)
        .where(
            Article.status == STATUS_PUBLISHED, Article.published_at >= start_utc
        )
        .order_by(Article.like_count.desc())
        .limit(limit)
    )
    items = [
        ContentRankItem(
            id=r.id,
            title=r.title,
            author_name=r.author_name,
            like_count=r.like_count or 0,
            view_count=r.view_count or 0,
            published_at=r.published_at,
        )
        for r in rows.all()
    ]

    try:
        await redis.set(cache_key, json.dumps([i.model_dump(mode="json") for i in items]), ex=_RANK_CACHE_TTL)
    except Exception:  # noqa: BLE001
        logger.warning("stats top-articles cache write failed", exc_info=True)

    return items


@router.get("/active-users", response_model=list[ActiveUserItem])
async def get_active_users(
    range: StatsRange = Query("30d", description="时间范围"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """活跃用户排行(按文章数,Redis 缓存 60s)。"""
    cache_key = f"stats:activeUsers:{range}:{limit}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            return [ActiveUserItem.model_validate(item) for item in json.loads(cached)]
    except Exception:  # noqa: BLE001
        logger.warning("stats active-users cache read failed, fallback to DB", exc_info=True)

    days = _DAYS.get(range, 30)
    start_utc, _now_utc = _parse_date_range(days)

    rows = await db.execute(
        select(
            User.id,
            User.nickname,
            func.count(Article.id).label("article_count"),
        )
        .join(Article, Article.author_id == User.id)
        .where(Article.created_at >= start_utc)
        .group_by(User.id, User.nickname)
        .order_by(func.count(Article.id).desc())
        .limit(limit)
    )
    items = [
        ActiveUserItem(
            user_id=r.id,
            nickname=r.nickname,
            article_count=r.article_count,
        )
        for r in rows.all()
    ]

    try:
        await redis.set(cache_key, json.dumps([i.model_dump(mode="json") for i in items]), ex=_RANK_CACHE_TTL)
    except Exception:  # noqa: BLE001
        logger.warning("stats active-users cache write failed", exc_info=True)

    return items
