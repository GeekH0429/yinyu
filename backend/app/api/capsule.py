"""时光胶囊路由:写给未来自己的信。

规则:
    - 封存后不可修改(写 → 封 → 等 → 开,一次性仪式);未开启前可放弃(删除)。
    - 未到期任何接口不下发 content(列表/详情一律 None),到期详情才带。
    - 到期提醒邮件由 main.py _capsule_notifier 调度器发,不在请求路径上。
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.time_capsule import TimeCapsule
from app.models.user import User
from app.schemas.capsule import CapsuleBrief, CapsuleCreate, CapsuleOut
from app.schemas.common import Page, offset_of

router = APIRouter(prefix="/capsules", tags=["时光胶囊"])


def _is_unlocked(c: TimeCapsule) -> bool:
    now = datetime.now(timezone.utc)
    ua = c.unlock_at if c.unlock_at.tzinfo else c.unlock_at.replace(tzinfo=timezone.utc)
    return ua <= now


def _brief(c: TimeCapsule) -> CapsuleBrief:
    return CapsuleBrief(
        id=c.id,
        title=c.title,
        unlock_at=c.unlock_at,
        is_unlocked=_is_unlocked(c),
        created_at=c.created_at,
    )


@router.post("", response_model=CapsuleOut, status_code=201)
async def create_capsule(
    data: CapsuleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """封存一封信。封存即不可改;unlock_at 校验见 schemas/capsule.py。"""
    c = TimeCapsule(
        user_id=user.id,
        title=data.title,
        content=data.content,
        unlock_at=data.unlock_at,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    out = CapsuleOut(**_brief(c).model_dump(), content=None, sealed=True)
    return out


@router.get("", response_model=Page[CapsuleBrief])
async def my_capsules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """我的胶囊列表(轻量,无 content)。最新写的在前。"""
    conds = [TimeCapsule.user_id == user.id]
    total = await db.scalar(select(func.count()).select_from(TimeCapsule).where(*conds))
    rows = await db.execute(
        select(TimeCapsule)
        .where(*conds)
        .order_by(TimeCapsule.created_at.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [_brief(c) for c in rows.scalars().all()]
    return Page[CapsuleBrief](items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/{capsule_id}", response_model=CapsuleOut)
async def get_capsule(
    capsule_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """详情:到期才带 content;封存中 content=None + sealed=true(正常业务态,不走 403)。"""
    c = await get_owned(
        db, TimeCapsule, capsule_id, user, owner_field="user_id",
        not_found="胶囊不存在", forbidden="只能查看自己的胶囊",
    )
    if _is_unlocked(c):
        return CapsuleOut(**_brief(c).model_dump(), content=c.content, sealed=False)
    return CapsuleOut(**_brief(c).model_dump(), content=None, sealed=True)


@router.delete("/{capsule_id}")
async def delete_capsule(
    capsule_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """放弃一枚胶囊(封存中/已开启都可删)。"""
    c = await get_owned(
        db, TimeCapsule, capsule_id, user, owner_field="user_id",
        not_found="胶囊不存在", forbidden="只能删除自己的胶囊",
    )
    await db.delete(c)
    await db.commit()
    return {"detail": "已删除"}
