"""评论 / 回复 / 点赞 触发通知的统一编排。

所有写入都在调用方的同一事务里,任一步失败整体回滚(通知永远不会脱离评论存在)。
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.comment import Comment
from app.models.notification import (
    NOTI_COMMENT,
    NOTI_COMMENT_LIKE,
    NOTI_REPLY,
    Notification,
)
from app.models.user import User
from app.services.comment_mention import _snippet, create_mention_notifications


async def fanout_comment_notifications(
    db: AsyncSession,
    *,
    comment: Comment,
    commenter: User,
    article: Article,
    parent: Comment | None,
    parent_author: User | None,
    mentioned_user_ids: list[int],
) -> None:
    """评论创建后调一次,把所有应发通知写进同一事务。

    规则:
      - 顶层评论 → 文章作者收一条 NOTI_COMMENT(自己评论自己文章不发)
      - 回复     → 被回复的顶层评论作者收一条 NOTI_REPLY(自己回复自己不发)
      - @提及    → 每个被 @用户收一条 NOTI_MENTION(去重 commenter 自己)
    """
    notis: list[Notification] = []
    snippet = _snippet(comment.content)

    if comment.parent_id is None:
        # 顶层评论 → 文章作者
        if article.author_id != commenter.id:
            notis.append(
                Notification(
                    recipient_id=article.author_id,
                    actor_id=commenter.id,
                    type=NOTI_COMMENT,
                    article_id=article.id,
                    comment_id=comment.id,
                    summary=snippet,
                )
            )
    else:
        # 回复 → 顶层评论作者
        if parent is not None and parent_author is not None:
            if parent.author_id != commenter.id:
                notis.append(
                    Notification(
                        recipient_id=parent.author_id,
                        actor_id=commenter.id,
                        type=NOTI_REPLY,
                        article_id=article.id,
                        comment_id=parent.id,
                        reply_comment_id=comment.id,
                        summary=snippet,
                    )
                )

    db.add_all(notis)

    # @提及
    await create_mention_notifications(
        db,
        comment=comment,
        commenter=commenter,
        article=article,
        mentioned_user_ids=mentioned_user_ids,
    )


async def create_comment_like_notification(
    db: AsyncSession,
    *,
    comment: Comment,
    commenter: User,
    article_id: int,
) -> Notification | None:
    """点赞评论 → 评论作者收 NOTI_COMMENT_LIKE。

    仅在「新增点赞」时调用(unlike 不发、不撤销已发通知)。
    自赞不发。V1 接受重复 like → 重复通知,不 dedup。
    """
    if comment.author_id == commenter.id:
        return None
    n = Notification(
        recipient_id=comment.author_id,
        actor_id=commenter.id,
        type=NOTI_COMMENT_LIKE,
        article_id=article_id,
        comment_id=comment.id,
        summary=_snippet(comment.content),
    )
    db.add(n)
    return n
