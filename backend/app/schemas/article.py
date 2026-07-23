"""图文阅读 schema。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.article import Article, STATUS_DRAFT
from app.models.user import User
from app.schemas.user import AuthorBrief

ArticleStatus = Literal["draft", "published"]


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str | None = Field(None, max_length=500)
    content_html: str = ""
    cover_url: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    status: ArticleStatus = STATUS_DRAFT


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    summary: str | None = Field(None, max_length=500)
    content_html: str | None = None
    cover_url: str | None = Field(None, max_length=500)
    tags: list[str] | None = None
    status: ArticleStatus | None = None


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
    published_at: datetime | None = None
    created_at: datetime
    author: AuthorBrief

    model_config = ConfigDict(from_attributes=True)


class ArticleOut(ArticleBrief):
    content_html: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagsOut(BaseModel):
    tags: list[str]


def to_brief(a: Article, author: User) -> ArticleBrief:
    """Article + 作者 → ArticleBrief 的唯一映射,供所有路由复用。"""
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
        published_at=a.published_at,
        created_at=a.created_at,
        author=AuthorBrief.model_validate(author),
    )


def to_out(a: Article, author: User) -> ArticleOut:
    return ArticleOut(
        **to_brief(a, author).model_dump(),
        content_html=a.content_html,
        updated_at=a.updated_at,
    )
