"""认证路由:注册(邀请码)、登录、刷新 token、改密、当前用户。"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, Unauthorized
from app.database import get_db
from app.deps import get_current_user
from app.redis_client import get_redis
from app.services.rate_limit import get_client_ip, sliding_limit
from app.models.invite import InviteCode
from app.models.user import ROLE_USER, User
from app.schemas.auth import (
    ChangePasswordIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenOut,
)
from app.schemas.user import UserOut
from app.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: RegisterIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await sliding_limit(
        redis, f"auth:register:{get_client_ip(request)}",
        max_attempts=10, window_seconds=60, lock_seconds=300,
    )
    # 用户名唯一性
    existed = await db.scalar(select(User).where(User.username == data.username))
    if existed is not None:
        raise Conflict("用户名已被占用")

    # 邀请码校验(行级锁,防止并发把次数刷爆)
    invite = await db.scalar(
        select(InviteCode).where(InviteCode.code == data.invite_code).with_for_update()
    )
    if invite is None or not invite.is_available():
        raise BadRequest("邀请码无效或已用尽")

    user = User(
        username=data.username,
        password_hash=await hash_password(data.password),
        nickname=data.nickname or data.username,
        role=ROLE_USER,
    )
    db.add(user)
    await db.flush()  # 拿到 user.id

    invite.used_count += 1
    if invite.used_count >= invite.max_uses:
        invite.is_active = False

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
async def login(
    data: LoginIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await sliding_limit(
        redis, f"auth:login:{get_client_ip(request)}",
        max_attempts=10, window_seconds=60, lock_seconds=300,
    )
    user = await db.scalar(
        select(User).where(or_(User.username == data.username, User.email == data.username))
    )
    if user is None or not await verify_password(data.password, user.password_hash):
        raise Unauthorized("用户名或密码错误")
    if not user.is_active:
        raise Unauthorized("账号已被禁用")
    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    data: RefreshIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await sliding_limit(
        redis, f"auth:refresh:{get_client_ip(request)}",
        max_attempts=20, window_seconds=60,
    )
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != TOKEN_TYPE_REFRESH:
            raise ValueError("wrong type")
        user_id = int(payload["sub"])
    except Exception as exc:  # noqa: BLE001
        raise Unauthorized("refresh token 无效或已过期") from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise Unauthorized()
    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.put("/password")
async def change_password(
    data: ChangePasswordIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await sliding_limit(
        redis, f"auth:pwd:{user.id}:{get_client_ip(request)}",
        max_attempts=5, window_seconds=60, lock_seconds=300,
    )
    if not await verify_password(data.old_password, user.password_hash):
        raise BadRequest("原密码错误")
    user.password_hash = await hash_password(data.new_password)
    await db.commit()
    return {"detail": "密码已更新"}
