"""图文阅读 schema。"""
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.article import Article, STATUS_DRAFT
from app.models.user import User
from app.schemas.user import AuthorBrief

ArticleStatus = Literal["draft", "published", "scheduled"]

# 定时时间须晚于当前时刻的缓冲:避免「写入瞬间已到期但发布器刚扫过」的语义模糊
_SCHEDULE_MIN_AHEAD = timedelta(seconds=60)


def _ensure_aware(dt: datetime) -> datetime:
    """naive 输入视为 UTC(正常前端应发带 offset 的 ISO 8601)。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _ensure_future(dt: datetime) -> datetime:
    if dt <= datetime.now(timezone.utc) + _SCHEDULE_MIN_AHEAD:
        raise ValueError("定时发布时间必须晚于当前时间(预留 1 分钟)")
    return dt


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str | None = Field(None, max_length=500)
    content_html: str = ""
    cover_url: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    status: ArticleStatus = STATUS_DRAFT
    scheduled_at: datetime | None = None

    @field_validator("scheduled_at")
    @classmethod
    def _normalize_scheduled_at(cls, v: datetime | None) -> datetime | None:
        return _ensure_aware(v) if v is not None else v

    @model_validator(mode="after")
    def _require_scheduled_at(self) -> "ArticleCreate":
        if self.status == "scheduled" and self.scheduled_at is None:
            raise ValueError("定时发布必须指定 scheduled_at")
        if self.scheduled_at is not None:
            _ensure_future(self.scheduled_at)
        return self


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    summary: str | None = Field(None, max_length=500)
    content_html: str | None = None
    cover_url: str | None = Field(None, max_length=500)
    tags: list[str] | None = None
    status: ArticleStatus | None = None
    scheduled_at: datetime | None = None

    @field_validator("scheduled_at")
    @classmethod
    def _normalize_scheduled_at(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        return _ensure_future(_ensure_aware(v))


class ArticleBrief(BaseModel):
    """列表用精简结构。"""
    id: int
    title: str
    summary: str | None = None
    cover_url: str | None = None
    tags: list[str] = []
    status: str
    view_count: int
    like_count: int
    comment_count: int = 0
    liked_by_me: bool = False
    published_at: datetime | None = None
    scheduled_at: datetime | None = None
    created_at: datetime
    author: AuthorBrief

    model_config = ConfigDict(from_attributes=True)


class ArticleOut(ArticleBrief):
    content_html: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagsOut(BaseModel):
    tags: list[str]


def to_brief(a: Article, author: User, *, liked_by_me: bool = False) -> ArticleBrief:
    """Article + 作者 → ArticleBrief 的唯一映射,供所有路由复用。

    `liked_by_me` 为关键字参数(默认 False),由调用方按当前 viewer 计算后传入;
    未登录场景或不关心点赞状态的接口(admin 列表)直接用默认值即可。
    """
    return ArticleBrief(
        id=a.id,
        title=a.title,
        summary=a.summary,
        cover_url=a.cover_url,
        tags=a.tags or [],
        status=a.status,
        view_count=a.view_count,
        like_count=a.like_count,
        comment_count=a.comment_count,
        liked_by_me=liked_by_me,
        published_at=a.published_at,
        scheduled_at=a.scheduled_at,
        created_at=a.created_at,
        author=AuthorBrief.model_validate(author),
    )


def to_out(a: Article, author: User, *, liked_by_me: bool = False) -> ArticleOut:
    return ArticleOut(
        **to_brief(a, author, liked_by_me=liked_by_me).model_dump(),
        content_html=a.content_html,
        updated_at=a.updated_at,
    )
