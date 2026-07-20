"""图文阅读模型(多用户共创平台:任何登录用户均可发布)。"""
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"


class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # PostgreSQL 数组类型,天然支持标签筛选
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list, server_default="{}")

    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_DRAFT, nullable=False, index=True
    )

    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ArticleLike(TimestampMixin, Base):
    __tablename__ = "article_likes"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_user_article"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
