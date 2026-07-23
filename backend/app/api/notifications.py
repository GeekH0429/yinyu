"""通知路由:列表 / 未读数 / 单条已读 / 全部已读。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.database import get_db
from app.deps import get_current_user
from app.models.article import Article
from app.models.comment import Comment
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import Page, offset_of
from app.schemas.notification import NotificationOut, to_notification_out

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=Page[NotificationOut])
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == user.id)
    )
    rows = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    notis = rows.scalars().all()

    # 批量取相关 actor / article.title / comment snippet(避免 N+1)
    actor_ids = {n.actor_id for n in notis if n.actor_id}
    article_ids = {n.article_id for n in notis if n.article_id}
    comment_ids = {n.comment_id for n in notis if n.comment_id}
    comment_ids |= {n.reply_comment_id for n in notis if n.reply_comment_id}

    actors: dict[int, User] = {}
    if actor_ids:
        rs = await db.execute(select(User).where(User.id.in_(actor_ids)))
        actors = {u.id: u for u in rs.scalars().all()}

    article_titles: dict[int, str] = {}
    if article_ids:
        rs = await db.execute(select(Article.id, Article.title).where(Article.id.in_(article_ids)))
        article_titles = {r[0]: r[1] for r in rs.all()}

    comment_snippets: dict[int, str] = {}
    if comment_ids:
        rs = await db.execute(select(Comment.id, Comment.content).where(Comment.id.in_(comment_ids)))
        comment_snippets = {r[0]: r[1][:80] for r in rs.all()}

    items = [
        to_notification_out(
            n,
            actor=actors.get(n.actor_id),
            article_title=article_titles.get(n.article_id) if n.article_id else None,
            comment_snippet=comment_snippets.get(n.comment_id) if n.comment_id else None,
        )
        for n in notis
    ]
    return Page[NotificationOut](
        items=items, total=total or 0, page=page, page_size=page_size
    )


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cnt = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read.is_(False))
    )
    return {"count": cnt or 0}


@router.post("/{noti_id}/read")
async def mark_read(
    noti_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    n = await db.get(Notification, noti_id)
    if n is None or n.recipient_id != user.id:
        raise NotFound("通知不存在")
    if not n.is_read:
        n.is_read = True
        await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True)
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    return {"ok": True}
