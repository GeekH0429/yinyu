"""暖话路由:场景列表 + 按场景随机抽取。

防搬运设计:
- 两个接口均需登录(get_current_user)
- 不提供 list 全量接口,只能逐条 random
- /scenes 只返回 count,不返回 text
- /random 每用户每自然日 30 次(sliding_limit)
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequest
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.warm_word import WarmWord
from app.redis_client import get_redis
from app.schemas.warm_word import SceneOut, WarmWordOut
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
        select(WarmWord.scene, func.count())
        .group_by(WarmWord.scene)
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

    return await pick_random(db, scene)
