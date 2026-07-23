"""通知 schema。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.notification import Notification
from app.models.user import User
from app.schemas.user import AuthorBrief

NotificationType = Literal["comment", "reply", "comment_like", "mention"]


class _ArticleRef(BaseModel):
    id: int
    title: str


class _CommentRef(BaseModel):
    id: int
    snippet: str  # 评论内容前 N 字


class NotificationOut(BaseModel):
    id: int
    type: NotificationType
    actor: AuthorBrief | None = None
    article: _ArticleRef | None = None
    comment: _CommentRef | None = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def to_notification_out(
    n: Notification,
    *,
    actor: User | None = None,
    article_title: str | None = None,
    comment_snippet: str | None = None,
) -> NotificationOut:
    """Notification → NotificationOut 的唯一映射。

    article_title / comment_snippet 由调用方按需 JOIN 后传入;若文章/评论已被级联
    删除(通知也会级联删,理论上不会到这里),传 None 即可。
    """
    article = None
    if n.article_id is not None and article_title is not None:
        article = _ArticleRef(id=n.article_id, title=article_title)
    comment = None
    if n.comment_id is not None and comment_snippet is not None:
        comment = _CommentRef(id=n.comment_id, snippet=comment_snippet)
    return NotificationOut(
        id=n.id,
        type=n.type,  # type: ignore[arg-type]
        actor=AuthorBrief.model_validate(actor) if actor else None,
        article=article,
        comment=comment,
        is_read=n.is_read,
        created_at=n.created_at,
    )
