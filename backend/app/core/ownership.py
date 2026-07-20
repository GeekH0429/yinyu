"""通用"归属权 + 管理员放行"校验(文章 / 树洞共用)。"""
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.exceptions import Forbidden, NotFound
from app.models.user import User


async def get_owned(
    db: AsyncSession,
    model: Type[DeclarativeBase],
    obj_id: int,
    user: User,
    *,
    not_found: str = "资源不存在",
    forbidden: str = "无权限",
):
    """加载对象;不存在 → 404;非作者且非管理员 → 403。"""
    obj = await db.get(model, obj_id)
    if obj is None:
        raise NotFound(not_found)
    if obj.author_id != user.id and not user.is_admin():  # type: ignore[attr-defined]
        raise Forbidden(forbidden)
    return obj
