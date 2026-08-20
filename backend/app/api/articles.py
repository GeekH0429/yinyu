"""图文阅读路由(多用户共创:登录后均可发布)。"""
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFound
from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.article import STATUS_PUBLISHED, STATUS_SCHEDULED, Article, ArticleLike
from app.models.user import User
from app.schemas.article import (
    ArticleBrief,
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    TagsOut,
    to_brief,
    to_out,
)
from app.schemas.common import Page, offset_of
from app.redis_client import get_redis
from app.services.email import notify_new_article
from app.services.rate_limit import get_client_ip
from app.services.view_counter import incr_view

router = APIRouter(prefix="/articles", tags=["图文阅读"])


@router.get("", response_model=Page[ArticleBrief])
async def list_published(
    tag: str | None = Query(None, description="标签筛选"),
    keyword: str | None = Query(None, description="标题/摘要关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """公共 feed:仅已发布,按发布时间倒序。"""
    base_conds = [Article.status == STATUS_PUBLISHED]
    if tag:
        base_conds.append(Article.tags.any(tag))  # tag = ANY(tags)

    if keyword:
        # OR → UNION:让 tags.any 分支独立走 GIN 索引,
        # title/summary 走 status BTree + ILIKE 过滤。
        # 原 OR 因 title/summary 无可用索引(前导通配 ILIKE 不能用 BTree),
        # 被规划器整体降级 Seq Scan,GIN 也跟着用不上。
        like = f"%{keyword}%"
        match_ids = (
            select(Article.id)
            .where(*base_conds, Article.title.ilike(like))
            .union(
                select(Article.id).where(*base_conds, Article.summary.ilike(like)),
                select(Article.id).where(*base_conds, Article.tags.any(keyword)),
            )
        ).subquery()
        total = await db.scalar(select(func.count()).select_from(match_ids))
        rows = await db.execute(
            select(Article, User)
            .join(match_ids, match_ids.c.id == Article.id)
            .join(User, User.id == Article.author_id)
            .order_by(Article.published_at.desc(), Article.id.desc())
            .offset(offset_of(page, page_size))
            .limit(page_size)
        )
    else:
        total = await db.scalar(select(func.count()).select_from(Article).where(*base_conds))
        rows = await db.execute(
            select(Article, User)
            .join(User, User.id == Article.author_id)
            .where(*base_conds)
            .order_by(Article.published_at.desc(), Article.id.desc())
            .offset(offset_of(page, page_size))
            .limit(page_size)
        )
    pairs = rows.all()
    # 批量查询当前用户对当页文章的点赞状态(1 次 IN 查询,避免 N+1)
    liked_ids: set[int] = set()
    if user and pairs:
        liked_rows = await db.execute(
            select(ArticleLike.article_id).where(
                ArticleLike.user_id == user.id,
                ArticleLike.article_id.in_([a.id for a, _ in pairs]),
            )
        )
        liked_ids = {r[0] for r in liked_rows.all()}
    items = [to_brief(a, u, liked_by_me=a.id in liked_ids) for a, u in pairs]
    return Page[ArticleBrief](items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/tags", response_model=TagsOut)
async def list_tags(db: AsyncSession = Depends(get_db)):
    """聚合所有已发布文章的标签(数据库内 unnest + 去重)。"""
    rows = await db.execute(
        select(func.unnest(Article.tags)).distinct().where(Article.status == STATUS_PUBLISHED)
    )
    tags = sorted({r[0] for r in rows.all()})
    return TagsOut(tags=tags)


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
    redis=Depends(get_redis),
):
    """详情:草稿仅作者/管理员可见;浏览量由 Redis 累积、后台批量回写。

    单次 LEFT JOIN 同时取 article + author + 当前用户点赞状态,
    替代原本的「主查询 + 再查一次点赞」两次 RTT。
    """
    # 未登录时用 -1 作为 user_id 条件,outerjoin 永不命中 → like_id 恒为 NULL
    uid = user.id if user else -1
    row = await db.execute(
        select(Article, User, ArticleLike.id.label("like_id"))
        .join(User, User.id == Article.author_id)
        .outerjoin(
            ArticleLike,
            (ArticleLike.user_id == uid) & (ArticleLike.article_id == Article.id),
        )
        .where(Article.id == article_id)
    )
    triple = row.first()
    if triple is None:
        raise NotFound("文章不存在")
    article, author, like_id = triple
    liked_by_me = like_id is not None

    if article.status != STATUS_PUBLISHED:
        if user is None or (user.id != article.author_id and not user.is_admin()):
            raise NotFound("文章不存在")

    viewer = str(user.id) if user else "ip:" + get_client_ip(request)
    await incr_view(redis, "article", article_id, viewer)
    article.view_count = (article.view_count or 0) + 1  # 内存校正(显示用),实际落库由后台回写

    return to_out(article, author, liked_by_me=liked_by_me)


@router.post("", response_model=ArticleOut, status_code=201)
async def create_article(
    data: ArticleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = Article(
        author_id=user.id,
        title=data.title,
        summary=data.summary,
        content_html=data.content_html,
        cover_url=data.cover_url,
        tags=data.tags or [],
        status=data.status,
        published_at=datetime.now(timezone.utc) if data.status == STATUS_PUBLISHED else None,
        scheduled_at=data.scheduled_at if data.status == STATUS_SCHEDULED else None,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    if article.status == STATUS_PUBLISHED:
        # commit 成功后再派发订阅邮件(只传纯值 id,避免 commit 后属性过期)
        asyncio.create_task(notify_new_article(article.id))
    return to_out(article, user)


@router.put("/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = await get_owned(db, Article, article_id, user, not_found="文章不存在", forbidden="只能操作自己的文章")
    payload = data.model_dump(exclude_unset=True)

    # 状态转换(需在 setattr 覆盖前读取 DB 旧值):
    #   → scheduled:必须有定时时间(没传则沿用历史值);定时即未发布,清 published_at
    #   → published:published_at 为空才补 now(重复保存不刷时间);清 scheduled_at
    #   → draft:取消定时,清 scheduled_at(published_at 保留,与下架语义一致)
    was_status = article.status
    new_status = payload.get("status")
    if new_status == STATUS_SCHEDULED:
        scheduled_at = payload.get("scheduled_at", article.scheduled_at)
        if scheduled_at is None:
            raise AppException(422, "定时发布必须指定时间", "SCHEDULED_AT_REQUIRED")
        payload["scheduled_at"] = scheduled_at
        payload["published_at"] = None
    elif new_status == STATUS_PUBLISHED:
        if article.published_at is None:
            payload["published_at"] = datetime.now(timezone.utc)
        payload["scheduled_at"] = None
    elif new_status is not None:  # draft
        payload["scheduled_at"] = None

    for k, v in payload.items():
        setattr(article, k, v)
    await db.commit()
    await db.refresh(article)
    if was_status != STATUS_PUBLISHED and article.status == STATUS_PUBLISHED:
        asyncio.create_task(notify_new_article(article.id))
    author = await db.get(User, article.author_id)
    liked_by_me = await db.scalar(
        select(ArticleLike.id).where(
            ArticleLike.user_id == user.id, ArticleLike.article_id == article_id
        )
    ) is not None
    return to_out(article, author, liked_by_me=liked_by_me)


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = await get_owned(db, Article, article_id, user, not_found="文章不存在", forbidden="只能操作自己的文章")
    await db.delete(article)
    await db.commit()
    return {"detail": "已删除"}


@router.post("/{article_id}/like")
async def toggle_like(
    article_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """点赞 / 取消点赞(切换)。"""
    article = await db.get(Article, article_id)
    if article is None or article.status != STATUS_PUBLISHED:
        raise NotFound("文章不存在")

    existed = await db.scalar(
        select(ArticleLike).where(
            ArticleLike.user_id == user.id, ArticleLike.article_id == article_id
        )
    )
    delta = -1 if existed else 1
    if existed:
        await db.delete(existed)
    else:
        db.add(ArticleLike(user_id=user.id, article_id=article_id))
    await db.execute(
        update(Article)
        .where(Article.id == article_id)
        .values(like_count=Article.like_count + delta)
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    return {"liked": delta > 0}
