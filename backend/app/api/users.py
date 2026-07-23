"""用户搜索路由(给评论 @提及下拉用)。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import AuthorBrief

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/search", response_model=list[AuthorBrief])
async def search_users(
    q: str = Query(..., min_length=1, max_length=40, description="nickname / username 前缀"),
    limit: int = Query(10, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """前缀模糊匹配 nickname / username,排除自己 + inactive。"""
    like = f"{q}%"
    rows = await db.execute(
        select(User)
        .where(
            User.id != user.id,
            User.is_active.is_(True),
            or_(User.nickname.ilike(like), User.username.ilike(like)),
        )
        .order_by(User.nickname.asc())
        .limit(limit)
    )
    return [AuthorBrief.model_validate(u) for u in rows.scalars().all()]
