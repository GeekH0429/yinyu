"""「我的」路由:个人资料、我发布的图文、我的树洞、我点赞的图文。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.database import get_db
from app.deps import get_current_user
from app.models.article import Article, ArticleLike
from app.models.treehole import TreeHole
from app.models.user import User
from app.schemas.article import ArticleBrief, to_brief
from app.schemas.common import Page, offset_of
from app.schemas.treehole import TreeHoleOut
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/me", tags=["我的"])


@router.get("", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("", response_model=UserOut)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.email and data.email != user.email:
        existed = await db.scalar(select(User).where(User.email == data.email))
        if existed is not None:
            raise Conflict("邮箱已被占用")
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/articles", response_model=Page[ArticleBrief])
async def my_articles(
    status: str | None = Query(None, description="draft/published"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conds = [Article.author_id == user.id]
    if status:
        conds.append(Article.status == status)
    total = await db.scalar(select(func.count()).select_from(Article).where(*conds))
    rows = await db.execute(
        select(Article)
        .where(*conds)
        .order_by(Article.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [to_brief(a, user) for a in rows.scalars().all()]
    return Page[ArticleBrief](items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/treeholes", response_model=Page[TreeHoleOut])
async def my_treeholes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conds = [TreeHole.author_id == user.id]
    total = await db.scalar(select(func.count()).select_from(TreeHole).where(*conds))
    rows = await db.execute(
        select(TreeHole)
        .where(*conds)
        .order_by(TreeHole.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [TreeHoleOut.model_validate(t) for t in rows.scalars().all()]
    return Page[TreeHoleOut](items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/likes", response_model=Page[ArticleBrief])
async def my_liked_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(
        select(func.count()).select_from(ArticleLike).where(ArticleLike.user_id == user.id)
    )
    rows = await db.execute(
        select(Article, User)
        .join(ArticleLike, ArticleLike.article_id == Article.id)
        .join(User, User.id == Article.author_id)
        .where(ArticleLike.user_id == user.id)
        .order_by(ArticleLike.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [to_brief(a, u) for a, u in rows.all()]
    return Page[ArticleBrief](items=items, total=total or 0, page=page, page_size=page_size)
