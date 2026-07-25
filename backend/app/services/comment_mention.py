"""评论创建时的 @提及解析 + 通知 fanout。

策略:前端传 mentioned_user_ids(从用户搜索下拉选择的真实用户 id),
后端不做文本匹配(避免 nickname 重名歧义)。
"""
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.comment import Comment
from app.models.notification import NOTI_MENTION, Notification
from app.models.user import User


class NotiTarget(NamedTuple):
    """事务外副作用(邮件提醒)用的轻量通知描述。

    用 NamedTuple 而非直接返回 Notification 对象,是因为 ORM 对象在
    commit 后属性会过期,async 下再访问会触发懒加载 → MissingGreenlet
    (见 CLAUDE.md「关键坑」)。所有字段在事务内构造时即固化。
    """

    recipient_id: int
    kind: str       # NOTI_COMMENT / NOTI_REPLY / NOTI_MENTION
    summary: str


def _snippet(text: str, n: int = 80) -> str:
    """评论摘要:超长截断。"""
    return text if len(text) <= n else text[: n - 1] + "…"


async def create_mention_notifications(
    db: AsyncSession,
    *,
    comment: Comment,
    commenter: User,
    article: Article,
    mentioned_user_ids: list[int],
) -> list[NotiTarget]:
    """为每个被 @的用户写一条 mention 通知。

    - 去重 commenter 自身(不能 @自己)
    - 去重 list 内重复
    - 校验用户存在(不存在的静默跳过 — 前端 bug 不应该 500)
    - 全部在调用方的同一事务里,统一 commit

    返回值:每个被 @用户的 NotiTarget(供 commit 后发邮件用),不返回 ORM 对象。
    """
    if not mentioned_user_ids:
        return []
    unique_ids = list({uid for uid in mentioned_user_ids if uid != commenter.id})
    if not unique_ids:
        return []
    rows = await db.execute(select(User).where(User.id.in_(unique_ids)))
    users = rows.scalars().all()
    snippet = _snippet(comment.content)
    notis: list[Notification] = []
    targets: list[NotiTarget] = []
    for u in users:
        notis.append(
            Notification(
                recipient_id=u.id,
                actor_id=commenter.id,
                type=NOTI_MENTION,
                article_id=article.id,
                comment_id=comment.id,
                is_read=False,
                summary=snippet,
            )
        )
        targets.append(NotiTarget(recipient_id=u.id, kind=NOTI_MENTION, summary=snippet))
    db.add_all(notis)
    return targets
