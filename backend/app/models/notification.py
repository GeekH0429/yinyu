"""通知模型:评论 / 回复 / 评论点赞 / @提及。"""
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

# 通知类型常量
NOTI_COMMENT = "comment"            # 有人评论了我的图文
NOTI_REPLY = "reply"                # 有人回复了我的评论
NOTI_COMMENT_LIKE = "comment_like"  # 有人点赞了我的评论
NOTI_MENTION = "mention"            # 在评论里 @了我

NOTI_TYPES = {NOTI_COMMENT, NOTI_REPLY, NOTI_COMMENT_LIKE, NOTI_MENTION}


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        # 未读数热路径:WHERE recipient_id=? AND is_read=false
        Index("ix_notifications_unread", "recipient_id", "is_read"),
        # 列表热路径:WHERE recipient_id=? ORDER BY created_at DESC
        Index("ix_notifications_recipient_created", "recipient_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True  # NULL=系统事件
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=True
    )
    # 主体评论(对于 reply 是被回复的评论;对于 comment/comment_like/mention 是触发的评论本身)
    comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    # 仅 type=reply 有值:指向触发回复本身(区别于 comment_id=被回复的评论)
    reply_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    # 反范式快照:列表展示时无需 JOIN。文章被删 → CASCADE 把通知也删掉(可接受)
    summary: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", server_default=""
    )
