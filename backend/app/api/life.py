"""人生时光轴路由:生日/人生长度设置、自定义人生节点。

    - 纯个人私密数据:只有本人能读写(get_owned,user_id 归属),无任何他人可见入口。
    - 默认学制节点(童年/幼儿园/…/大学)不入库 —— App 端按生日推算(见 schemas/life.py 注释)。
    - GET 聚合一次带回胶囊落点与写作足迹(只回时间/标题,胶囊 content 服务端强制不下发)。
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ownership import get_owned
from app.database import get_db
from app.deps import get_current_user
from app.models.article import Article
from app.models.life_milestone import LifeMilestone
from app.models.time_capsule import TimeCapsule
from app.models.user import User
from app.schemas.life import (
    ArticleMarkOut,
    CapsuleMarkOut,
    LifeMilestoneCreate,
    LifeMilestoneOut,
    LifeMilestoneUpdate,
    LifeOut,
    LifeSettingsUpdate,
)

router = APIRouter(prefix="/me/life", tags=["人生时光轴"])


@router.get("", response_model=LifeOut)
async def get_life(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """时光轴聚合:设置 + 自定义节点 + 胶囊落点 + 写作足迹。"""
    milestone_rows = await db.execute(
        select(LifeMilestone)
        .where(LifeMilestone.user_id == user.id)
        .order_by(LifeMilestone.start_date)
    )
    milestones = [LifeMilestoneOut.model_validate(m) for m in milestone_rows.scalars().all()]

    # 胶囊落点:全部胶囊(未来=将收到的信,过去=已开启的信);只取时间与标题
    capsule_rows = await db.execute(
        select(TimeCapsule.id, TimeCapsule.title, TimeCapsule.unlock_at)
        .where(TimeCapsule.user_id == user.id)
        .order_by(TimeCapsule.unlock_at)
    )
    capsules = [CapsuleMarkOut(id=r.id, title=r.title, unlock_at=r.unlock_at) for r in capsule_rows.all()]

    # 写作足迹:已发布图文的发布时刻
    article_rows = await db.execute(
        select(Article.id, Article.title, Article.published_at)
        .where(Article.author_id == user.id, Article.status == "published", Article.published_at.isnot(None))
        .order_by(Article.published_at)
    )
    articles = [ArticleMarkOut(id=r.id, title=r.title, published_at=r.published_at) for r in article_rows.all()]

    return LifeOut(
        birthday=user.birthday,
        lifespan_years=user.lifespan_years,
        milestones=milestones,
        capsules=capsules,
        articles=articles,
    )


@router.put("", response_model=LifeOut)
async def update_life_settings(
    data: LifeSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新生日 / 人生长度(exclude_unset,两者可分别改)。"""
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(user, k, v)
    await db.commit()
    return await get_life(user=user, db=db)


@router.post("/milestones", response_model=LifeMilestoneOut, status_code=201)
async def create_milestone(
    data: LifeMilestoneCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m = LifeMilestone(
        user_id=user.id,
        label=data.label,
        color=data.color,
        start_date=data.start_date,
        end_date=data.end_date,
        site=data.site,
        images=data.images,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@router.put("/milestones/{milestone_id}", response_model=LifeMilestoneOut)
async def update_milestone(
    milestone_id: int,
    data: LifeMilestoneUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m = await get_owned(
        db, LifeMilestone, milestone_id, user, owner_field="user_id",
        not_found="节点不存在", forbidden="只能修改自己的节点",
    )
    m.label = data.label
    m.color = data.color
    m.start_date = data.start_date
    m.end_date = data.end_date
    m.site = data.site
    m.images = data.images
    await db.commit()
    await db.refresh(m)
    return m


@router.delete("/milestones/{milestone_id}")
async def delete_milestone(
    milestone_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m = await get_owned(
        db, LifeMilestone, milestone_id, user, owner_field="user_id",
        not_found="节点不存在", forbidden="只能删除自己的节点",
    )
    await db.delete(m)
    await db.commit()
    return {"detail": "已删除"}
