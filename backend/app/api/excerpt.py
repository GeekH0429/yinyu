"""摘抄路由:阅读时收藏的句子(个人笔记本)。

    - 任何人只能读/删自己的(get_owned,user_id 归属)。
    - article_id 只存快照不做外键;文章删除后摘抄仍在(见 models/excerpt.py)。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.excerpt import Excerpt
from app.models.user import User
from app.schemas.common import Page, offset_of
from app.schemas.excerpt import ExcerptCreate, ExcerptOut

router = APIRouter(prefix="/excerpts", tags=["摘抄"])


@router.post("", response_model=ExcerptOut, status_code=201)
async def create_excerpt(
    data: ExcerptCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    e = Excerpt(
        user_id=user.id,
        article_id=data.article_id,
        article_title=data.article_title,
        content=data.content,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


@router.get("", response_model=Page[ExcerptOut])
async def my_excerpts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conds = [Excerpt.user_id == user.id]
    total = await db.scalar(select(func.count()).select_from(Excerpt).where(*conds))
    rows = await db.execute(
        select(Excerpt)
        .where(*conds)
        .order_by(Excerpt.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [ExcerptOut.model_validate(e) for e in rows.scalars().all()]
    return Page[ExcerptOut](items=items, total=total or 0, page=page, page_size=page_size)


@router.delete("/{excerpt_id}")
async def delete_excerpt(
    excerpt_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    e = await get_owned(
        db, Excerpt, excerpt_id, user, owner_field="user_id",
        not_found="摘抄不存在", forbidden="只能删除自己的摘抄",
    )
    await db.delete(e)
    await db.commit()
    return {"detail": "已删除"}
