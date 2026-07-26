"""暖话路由:场景列表 + 按场景随机 + 收藏夹。

防搬运设计:
- 所有接口均需登录(get_current_user)
- 不提供 list 全量接口,只能逐条 random
- /scenes 只返回 count,不返回 text
- /random 每用户每自然日 30 次(sliding_limit)
- 收藏夹仅返回当前用户自己的记录
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequest, NotFound
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.warm_word import WarmWord
from app.models.warm_word_favorite import WarmWordFavorite
from app.redis_client import get_redis
from app.schemas.common import Page, offset_of
from app.schemas.warm_word import FavoriteOut, SceneOut, WarmWordOut
from app.services.rate_limit import sliding_limit
from app.services.warm_word import SCENES, pick_random

router = APIRouter(prefix="/warm_words", tags=["暖话"])

# 北京时间 UTC+8(项目默认时区)
_CN_TZ = timezone(timedelta(hours=8))


@router.get("/scenes", response_model=list[SceneOut])
async def list_scenes(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有可用场景及其暖话条数(需登录)。"""
    rows = await db.execute(
        select(WarmWord.scene, func.count()).group_by(WarmWord.scene)
    )
    counts = {scene: cnt for scene, cnt in rows.all()}
    # 用 SCENES dict 保证固定展示顺序 + 缺语料的场景也出现(count=0)
    return [
        SceneOut(scene=scene, label=label, count=int(counts.get(scene, 0)))
        for scene, label in SCENES.items()
    ]


@router.get("/random", response_model=WarmWordOut)
async def get_random(
    scene: str = Query(..., description="场景,如 anxiety/lonely/insomnia"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """按场景随机抽一条暖话(需登录 + 每自然日 30 次限流)。"""
    if scene not in SCENES:
        raise BadRequest("场景不存在")

    # 自然日限流:key 带日期,window 设 2 天保险过期
    today = datetime.now(_CN_TZ).strftime("%Y-%m-%d")
    await sliding_limit(
        redis,
        f"ww:random:{user.id}:{today}",
        max_attempts=settings.warm_words_daily_limit,
        window_seconds=settings.warm_words_scene_window_seconds * 2,
        lock_seconds=0,
        message="今日暖话已读完,明天再来吧",
    )

    ww = await pick_random(db, scene)
    # 注入收藏状态
    fav_id = await db.scalar(
        select(WarmWordFavorite.id).where(
            WarmWordFavorite.user_id == user.id,
            WarmWordFavorite.warm_word_id == ww.id,
        )
    )
    out = WarmWordOut.model_validate(ww)
    out.is_favorited = fav_id is not None
    return out


@router.get("/favorites", response_model=Page[FavoriteOut])
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出我收藏的暖话(分页,按收藏时间倒序)。"""
    conds = [WarmWordFavorite.user_id == user.id]
    total = await db.scalar(
        select(func.count()).select_from(WarmWordFavorite).where(*conds)
    )
    rows = await db.execute(
        select(
            WarmWordFavorite.id,
            WarmWordFavorite.warm_word_id,
            WarmWord.scene,
            WarmWord.text,
            WarmWordFavorite.created_at,
        )
        .join(WarmWord, WarmWord.id == WarmWordFavorite.warm_word_id)
        .where(*conds)
        .order_by(WarmWordFavorite.created_at.desc(), WarmWordFavorite.id.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [
        FavoriteOut(
            id=r.id,
            warm_word_id=r.warm_word_id,
            scene=r.scene,
            text=r.text,
            created_at=r.created_at,
        )
        for r in rows.all()
    ]
    return Page[FavoriteOut](
        items=items, total=total or 0, page=page, page_size=page_size
    )


@router.post("/{warm_word_id}/favorite", response_model=FavoriteOut)
async def create_favorite(
    warm_word_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """收藏一条暖话(幂等:已收藏直接返回)。"""
    ww = await db.get(WarmWord, warm_word_id)
    if ww is None:
        raise NotFound("暖话不存在")

    existing = await db.scalar(
        select(WarmWordFavorite).where(
            WarmWordFavorite.user_id == user.id,
            WarmWordFavorite.warm_word_id == warm_word_id,
        )
    )
    if existing:
        return FavoriteOut(
            id=existing.id,
            warm_word_id=warm_word_id,
            scene=ww.scene,
            text=ww.text,
            created_at=existing.created_at,
        )

    fav = WarmWordFavorite(user_id=user.id, warm_word_id=warm_word_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return FavoriteOut(
        id=fav.id,
        warm_word_id=warm_word_id,
        scene=ww.scene,
        text=ww.text,
        created_at=fav.created_at,
    )


@router.delete("/{warm_word_id}/favorite")
async def delete_favorite(
    warm_word_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏(幂等:不存在也返回 ok)。"""
    fav = await db.scalar(
        select(WarmWordFavorite).where(
            WarmWordFavorite.user_id == user.id,
            WarmWordFavorite.warm_word_id == warm_word_id,
        )
    )
    if fav is not None:
        await db.delete(fav)
        await db.commit()
    return {"ok": True}
