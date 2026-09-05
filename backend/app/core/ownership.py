"""通用"归属权 + 管理员放行"校验(文章 / 树洞 / 时光胶囊共用)。"""
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
    owner_field: str = "author_id",
    not_found: str = "资源不存在",
    forbidden: str = "无权限",
):
    """加载对象;不存在 → 404;非属主且非管理员 → 403。

    owner_field:归属字段名。文章/树洞是 author_id(默认);TimeCapsule 用 user_id。
    """
    obj = await db.get(model, obj_id)
    if obj is None:
        raise NotFound(not_found)
    if getattr(obj, owner_field) != user.id and not user.is_admin():  # type: ignore[attr-defined]
        raise Forbidden(forbidden)
    return obj
