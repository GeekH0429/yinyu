"""评论路由:列表 / 创建 / 点赞 / 删除。

挂在 /articles/{article_id}/comments 与 /comments 下。
读 / 写均需登录(yinyu 全站登录才能阅读,与现有约定一致)。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequest, NotFound
from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.article import STATUS_PUBLISHED, Article
from app.models.comment import Comment, CommentLike
from app.models.user import User
from app.redis_client import get_redis
from app.schemas.comment import CommentCreate, CommentOut, to_comment_out
from app.schemas.common import Page, offset_of
from app.services.comment_notify import (
    create_comment_like_notification,
    fanout_comment_notifications,
)
from app.services.rate_limit import sliding_limit

router = APIRouter(tags=["评论"])


# ---------- 列表 ----------

@router.get("/articles/{article_id}/comments", response_model=Page[CommentOut])
async def list_comments(
    article_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分页顶层评论,按需拉取其全部回复。

    返回扁平列表:顺序为 [T1, R1, R2, T2, R3, ...](顶层 + 各自回复紧随),
    客户端按 parent_id 分组渲染即可。
    """
    article = await db.get(Article, article_id)
    if article is None or article.status != STATUS_PUBLISHED:
        raise NotFound("文章不存在")

    # 1. 分页顶层评论
    total = await db.scalar(
        select(func.count())
        .select_from(Comment)
        .where(Comment.article_id == article_id, Comment.parent_id.is_(None))
    )
    top_rows = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(Comment.article_id == article_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    top_pairs = top_rows.all()
    top_ids = [c.id for c, _ in top_pairs]

    # 2. 一次性拉取本页顶层评论的所有回复
    reply_pairs: list = []
    if top_ids:
        r_rows = await db.execute(
            select(Comment, User)
            .join(User, User.id == Comment.author_id)
            .where(Comment.parent_id.in_(top_ids))
            .order_by(Comment.parent_id.asc(), Comment.created_at.asc())
        )
        reply_pairs = r_rows.all()

    # 3. 组装扁平列表:[T1, R1, R2, T2, R3, ...]
    replies_by_parent: dict[int, list] = {}
    for pair in reply_pairs:
        c = pair[0]
        replies_by_parent.setdefault(c.parent_id, []).append(pair)

    flat_pairs: list = []
    for top_pair in top_pairs:
        flat_pairs.append(top_pair)
        top_id = top_pair[0].id
        flat_pairs.extend(replies_by_parent.get(top_id, []))

    # 4. 批量取相关 User(author / reply_to)避免 N+1
    all_ids = [c.id for c, _ in flat_pairs]
    reply_to_ids = [c.reply_to_user_id for c, _ in flat_pairs if c.reply_to_user_id]
    author_ids = {c.author_id for c, _ in flat_pairs}
    extra_uids = list(author_ids | set(reply_to_ids))

    users_map: dict[int, User] = {}
    if extra_uids:
        u_rows = await db.execute(select(User).where(User.id.in_(extra_uids)))
        users_map = {u.id: u for u in u_rows.scalars().all()}

    # 5. 当前用户点赞的 comment_id 集合
    liked_ids: set[int] = set()
    if all_ids:
        like_rows = await db.execute(
            select(CommentLike.comment_id).where(
                CommentLike.user_id == user.id, CommentLike.comment_id.in_(all_ids)
            )
        )
        liked_ids = {r[0] for r in like_rows.all()}

    items = [
        to_comment_out(
            c,
            users_map.get(c.author_id) or au,
            reply_to=users_map.get(c.reply_to_user_id) if c.reply_to_user_id else None,
            liked_by_me=c.id in liked_ids,
        )
        for c, au in flat_pairs
    ]
    # total 是顶层评论数,供分页器使用
    return Page[CommentOut](
        items=items, total=total or 0, page=page, page_size=page_size
    )


# ---------- 创建 ----------

@router.post("/articles/{article_id}/comments", response_model=CommentOut, status_code=201)
async def create_comment(
    article_id: int,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    article = await db.get(Article, article_id)
    if article is None or article.status != STATUS_PUBLISHED:
        raise NotFound("文章不存在")

    # 限流:每用户 60s 内最多 5 次,超限锁 300s
    await sliding_limit(
        redis,
        f"cmt:{user.id}",
        max_attempts=settings.comment_max_attempts,
        window_seconds=settings.comment_attempt_window_seconds,
        lock_seconds=settings.comment_lock_seconds,
        message="评论过于频繁,请稍后再试",
    )

    parent: Comment | None = None
    parent_author: User | None = None
    if data.parent_id is not None:
        parent = await db.get(Comment, data.parent_id)
        if parent is None or parent.article_id != article_id:
            raise BadRequest("回复目标评论不存在")
        if parent.parent_id is not None:
            raise BadRequest("只支持一层回复")
        parent_author = await db.get(User, parent.author_id)
        # reply_to_user_id 校验
        rt = data.reply_to_user_id
        if rt is not None and rt != parent.author_id:
            rt_user = await db.get(User, rt)
            if rt_user is None:
                raise BadRequest("被回复用户不存在")

    comment = Comment(
        article_id=article_id,
        author_id=user.id,
        parent_id=data.parent_id,
        reply_to_user_id=data.reply_to_user_id if data.parent_id is not None else None,
        content=data.content,
        like_count=0,
    )
    db.add(comment)

    # 原子 +1(必须 synchronize_session=False)
    await db.execute(
        update(Article)
        .where(Article.id == article_id)
        .values(comment_count=Article.comment_count + 1)
        .execution_options(synchronize_session=False)
    )

    # 先 flush 拿到 comment.id,再写通知(都在同一事务)
    await db.flush()

    await fanout_comment_notifications(
        db,
        comment=comment,
        commenter=user,
        article=article,
        parent=parent,
        parent_author=parent_author,
        mentioned_user_ids=data.mentioned_user_ids,
    )

    await db.commit()
    await db.refresh(comment)

    return to_comment_out(
        comment,
        user,
        reply_to=(
            parent_author
            if parent_author and parent_author.id != user.id and data.reply_to_user_id is not None
            else None
        ),
    )


# ---------- 点赞 ----------

@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """点赞 / 取消点赞(切换)。仅新增点赞时发通知,unlike 不撤销。"""
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise NotFound("评论不存在")

    existed = await db.scalar(
        select(CommentLike).where(
            CommentLike.user_id == user.id, CommentLike.comment_id == comment_id
        )
    )
    delta = -1 if existed else 1
    if existed:
        await db.delete(existed)
    else:
        db.add(CommentLike(user_id=user.id, comment_id=comment_id))

    await db.execute(
        update(Comment)
        .where(Comment.id == comment_id)
        .values(like_count=Comment.like_count + delta)
        .execution_options(synchronize_session=False)
    )

    # 仅「新增点赞」时发通知
    if not existed:
        await create_comment_like_notification(
            db, comment=comment, commenter=user, article_id=comment.article_id
        )

    await db.commit()
    return {"liked": delta > 0}


# ---------- 删除 ----------

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # get_owned 自动校验作者或管理员(Comment 必须有 author_id 字段)
    comment = await get_owned(
        db,
        Comment,
        comment_id,
        user,
        not_found="评论不存在",
        forbidden="只能删除自己的评论",
    )
    article_id = comment.article_id
    # 删前先数直接子评论(yinyu 只支持一层回复,parent_id 有 ON DELETE CASCADE
    # 会自动级联删除子评论,但 Article.comment_count 需要手动减去对应数量,
    # 否则会与实际行数漂移)
    child_count = await db.scalar(
        select(func.count()).select_from(Comment).where(Comment.parent_id == comment_id)
    ) or 0
    # 硬删除(级联删 comment_likes 与子回复 — parent_id 有 ON DELETE CASCADE)
    await db.delete(comment)

    # 原子 -(1 + child_count),带 >= delta 守卫防负
    delta = 1 + child_count
    await db.execute(
        update(Article)
        .where(Article.id == article_id, Article.comment_count >= delta)
        .values(comment_count=Article.comment_count - delta)
        .execution_options(synchronize_session=False)
    )

    await db.commit()
    return {"ok": True}
