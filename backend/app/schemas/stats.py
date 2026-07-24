"""统计数据 Schema。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

StatsRange = Literal["7d", "30d", "90d"]


class TrendPoint(BaseModel):
    """趋势数据点(按日期的计数)。"""
    date: str  # YYYY-MM-DD
    count: int


class OverviewOut(BaseModel):
    """总体概览响应。"""
    total_users: int
    total_articles: int
    total_published: int
    total_treeholes: int
    total_media: int
    new_users: int
    new_articles: int
    new_treeholes: int
    total_views: int
    total_likes: int
    total_storage_bytes: int


class TrendOut(BaseModel):
    """趋势数据响应。"""
    users: list[TrendPoint]
    articles: list[TrendPoint]
    treeholes: list[TrendPoint]


class ContentRankItem(BaseModel):
    """内容排行项。"""
    id: int
    title: str
    author_name: str
    like_count: int
    view_count: int
    published_at: datetime | None = None


class ActiveUserItem(BaseModel):
    """活跃用户排行项(按文章数)。"""
    user_id: int
    nickname: str
    article_count: int