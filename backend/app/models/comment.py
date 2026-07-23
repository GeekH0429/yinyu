"""评论模型(单层回复:顶层评论 + 一层回复,不再嵌套)。"""
from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        # 顶层评论列表热路径:WHERE article_id=? AND parent_id IS NULL ORDER BY created_at
        Index(
            "ix_comments_toplevel",
            "article_id",
            "created_at",
            postgresql_where=text("parent_id IS NULL"),
        ),
        # 回复列表热路径:按 parent_id 取所有回复
        Index("ix_comments_parent", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 命名为 author_id 以复用 core/ownership.get_owned(模型需有 author_id 属性)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # NULL=顶层评论;非 NULL=回复(服务层校验 parent.parent_id IS NULL,拒绝多层)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    # 被回复的用户(仅回复有值;用于显示「@xxx」,可与 parent.author 不同:
    # 在 A 的顶层评论下回复了 B 的回复,parent=A 的评论,reply_to_user=B)
    reply_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )


class CommentLike(TimestampMixin, Base):
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_comment_likes_user_comment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), index=True, nullable=False
    )
