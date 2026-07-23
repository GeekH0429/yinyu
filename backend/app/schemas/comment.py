"""评论 schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.comment import Comment
from app.models.user import User
from app.schemas.user import AuthorBrief


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, strip_whitespace=True)
    parent_id: int | None = Field(
        None, description="回复目标顶层评论 id;顶层评论省略"
    )
    reply_to_user_id: int | None = Field(
        None, description="被回复用户 id(仅回复时有值)"
    )
    mentioned_user_ids: list[int] = Field(
        default_factory=list, max_length=10, description="前端 @选择器选中的用户 id"
    )


class CommentOut(BaseModel):
    id: int
    article_id: int
    author: AuthorBrief
    content: str
    parent_id: int | None = None
    reply_to: AuthorBrief | None = None
    mentioned_users: list[AuthorBrief] = []
    like_count: int
    liked_by_me: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def to_comment_out(
    c: Comment,
    author: User,
    *,
    reply_to: User | None = None,
    mentioned_users: list[User] | None = None,
    liked_by_me: bool = False,
) -> CommentOut:
    """Comment + 作者 → CommentOut 的唯一映射,所有路由复用。"""
    return CommentOut(
        id=c.id,
        article_id=c.article_id,
        author=AuthorBrief.model_validate(author),
        content=c.content,
        parent_id=c.parent_id,
        reply_to=AuthorBrief.model_validate(reply_to) if reply_to else None,
        mentioned_users=[AuthorBrief.model_validate(u) for u in (mentioned_users or [])],
        like_count=c.like_count,
        liked_by_me=liked_by_me,
        created_at=c.created_at,
    )
