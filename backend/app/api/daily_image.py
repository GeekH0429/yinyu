"""每日一图公开路由(今日图 + 历史回溯)。

无鉴权:启动即可拉取,App 在首页 onShow 触发。
时区:服务器按北京时间(UTC+8)算「今天」,客户端不传日期。
"""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.daily_image import DailyImage
from app.schemas.common import Page, offset_of
from app.schemas.daily_image import DailyImageOut

router = APIRouter(prefix="/daily-images", tags=["每日一图"])

# 北京时间 UTC+8(项目默认时区,封闭社区全在国内)
CN_TZ = timezone(timedelta(hours=8))


def _cn_today() -> date:
    """服务器当前北京时间对应的日期。"""
    return datetime.now(CN_TZ).date()


@router.get("/today", response_model=DailyImageOut)
async def get_today(db: AsyncSession = Depends(get_db)):
    """返回今日的每日一图;当天未排期 -> 404(App 静默跳过弹层)。"""
    today = _cn_today()
    row = await db.execute(
        select(DailyImage).where(DailyImage.publish_date == today)
    )
    di = row.scalar_one_or_none()
    if di is None:
        from app.core.exceptions import NotFound

        raise NotFound("今日未排期")
    return di


@router.get("/history", response_model=Page[DailyImageOut])
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """历史回溯:仅返回 publish_date <= 今天 的记录,按日期倒序分页。"""
    today = _cn_today()
    conds = [DailyImage.publish_date <= today]
    total = await db.scalar(
        select(func.count()).select_from(DailyImage).where(*conds)
    )
    rows = await db.execute(
        select(DailyImage)
        .where(*conds)
        .order_by(DailyImage.publish_date.desc(), DailyImage.id.desc())
        .offset(offset_of(page, page_size))
        .limit(page_size)
    )
    items = [DailyImageOut.model_validate(d) for d in rows.scalars().all()]
    return Page[DailyImageOut](
        items=items, total=total or 0, page=page, page_size=page_size
    )
