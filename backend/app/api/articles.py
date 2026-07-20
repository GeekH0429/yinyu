"""图文阅读路由(多用户共创:登录后均可发布)。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.article import STATUS_PUBLISHED, Article, ArticleLike
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

router = APIRouter(prefix="/articles", tags=["图文阅读"])


@router.get("", response_model=Page[ArticleBrief])
async def list_published(
    tag: str | None = Query(None, description="标签筛选"),
    keyword: str | None = Query(None, description="标题/摘要关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """公共 feed:仅已发布,按发布时间倒序。"""
    conds = [Article.status == STATUS_PUBLISHED]
    if tag:
        conds.append(Article.tags.any(tag))  # tag = ANY(tags)
    if keyword:
        like = f"%{keyword}%"
        conds.append(or_(Article.title.ilike(like), Article.summary.ilike(like)))

    total = await db.scalar(select(func.count()).select_from(Article).where(*conds))
    rows = await db.execute(
        select(Article, User)
        .join(User, User.id == Article.author_id)
        .where(*conds)
        .order_by(Article.published_at.desc().nulls_last(), Article.id.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [to_brief(a, u) for a, u in rows.all()]
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
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """详情:草稿仅作者/管理员可见;浏览量原子自增。"""
    row = await db.execute(
        select(Article, User).join(User, User.id == Article.author_id).where(Article.id == article_id)
    )
    pair = row.first()
    if pair is None:
        raise NotFound("文章不存在")
    article, author = pair

    if article.status != STATUS_PUBLISHED:
        if user is None or (user.id != article.author_id and not user.is_admin()):
            raise NotFound("文章不存在")

    await db.execute(
        update(Article)
        .where(Article.id == article_id)
        .values(view_count=Article.view_count + 1)
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    article.view_count = (article.view_count or 0) + 1  # 内存校正,避免再次 IO

    return to_out(article, author)


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
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
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

    # 草稿转发布时补上 published_at(status 合法性由 schema 的 Literal 保证)
    if payload.get("status") == STATUS_PUBLISHED and article.published_at is None:
        payload["published_at"] = datetime.now(timezone.utc)

    for k, v in payload.items():
        setattr(article, k, v)
    await db.commit()
    await db.refresh(article)
    author = await db.get(User, article.author_id)
    return to_out(article, author)


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
