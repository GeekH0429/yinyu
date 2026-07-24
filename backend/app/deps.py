"""FastAPI 依赖:数据库、当前用户、管理员守卫。"""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import Forbidden, Unauthorized
from app.database import get_db
from app.models.user import User
from app.security import TOKEN_TYPE_ACCESS, decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=True,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            raise ValueError("wrong token type")
        user_id = int(payload["sub"])
    except Exception as exc:  # noqa: BLE001
        raise Unauthorized("登录已过期,请重新登录") from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise Unauthorized("用户不存在或已被禁用")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin():
        raise Forbidden("需要管理员权限")
    return user
