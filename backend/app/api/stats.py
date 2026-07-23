"""统计数据路由。"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.articles import STATUS_PUBLISHED
from app.database import get_db
from app.deps import require_admin
from app.models.article import Article
from app.models.media import Media
from app.models.treehole import TreeHole
from app.models.user import User
from app.schemas.stats import (
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

# 北京时区
CN_TZ = timezone(timedelta(hours=8))

StatsRange = str  # Literal["7d", "30d", "90d"]


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


@router.get("/overview", response_model=OverviewOut)
async def get_overview(
    range: StatsRange = Query("30d", description="时间范围"),
    db: AsyncSession = Depends(get_db),
):
    """总体概览:用户数/文章数/树洞数等关键指标。"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 30)
    start_utc, now_utc = _parse_date_range(days)

    # 总数统计
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_articles = await db.scalar(select(func.count()).select_from(Article))
    total_published = await db.scalar(
        select(func.count())
        .select_from(Article)
        .where(Article.status == STATUS_PUBLISHED)
    )
    total_treeholes = await db.scalar(select(func.count()).select_from(TreeHole))
    total_media = await db.scalar(select(func.count()).select_from(Media))

    # 时间范围内新增
    new_users = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= start_utc)
    )
    new_articles = await db.scalar(
        select(func.count())
        .select_from(Article)
        .where(Article.created_at >= start_utc)
    )
    new_treeholes = await db.scalar(
        select(func.count())
        .select_from(TreeHole)
        .where(TreeHole.created_at >= start_utc)
    )

    # 内容互动总量(浏览/点赞)
    total_views = await db.scalar(
        select(func.coalesce(func.sum(Article.view_count), 0)).select_from(Article)
    )
    total_likes = await db.scalar(
        select(func.coalesce(func.sum(Article.like_count), 0)).select_from(Article)
    )

    # 存储统计
    total_storage = await db.scalar(
        select(func.coalesce(func.sum(Media.size_bytes), 0)).select_from(Media)
    )

    return OverviewOut(
        total_users=total_users or 0,
        total_articles=total_articles or 0,
        total_published=total_published or 0,
        total_treeholes=total_treeholes or 0,
        total_media=total_media or 0,
        new_users=new_users or 0,
        new_articles=new_articles or 0,
        new_treeholes=new_treeholes or 0,
        total_views=total_views or 0,
        total_likes=total_likes or 0,
        total_storage_bytes=total_storage or 0,
    )


@router.get("/trends", response_model=TrendOut)
async def get_trends(
    range: StatsRange = Query("30d", description="时间范围"),
    db: AsyncSession = Depends(get_db),
):
    """用户增长与内容发布趋势(按日期分组)。"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 30)
    start_utc, now_utc = _parse_date_range(days)

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


@router.get("/top-articles", response_model=list[ContentRankItem])
async def get_top_articles(
    range: StatsRange = Query("30d", description="时间范围"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
):
    """热门文章排行(按点赞数)。"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 30)
    start_utc, now_utc = _parse_date_range(days)

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

    return [
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


@router.get("/active-users", response_model=list[ContentRankItem])
async def get_active_users(
    range: StatsRange = Query("30d", description="时间范围"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
):
    """活跃用户排行(按文章数)。"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 30)
    start_utc, now_utc = _parse_date_range(days)

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

    return [
        ContentRankItem(
            id=r.id,
            title=r.nickname,
            author_name=r.nickname,
            like_count=r.article_count,
            view_count=0,
            published_at=None,
        )
        for r in rows.all()
    ]