"""文章按日浏览量归档表(每日凌晨由后台任务从 Redis 同步)。"""
from datetime import date

from sqlalchemy import Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ArticleDailyView(Base):
    """每天一行,记录当天全站文章总浏览量。

    数据源是 Redis `view:daily:article:{YYYYMMDD}`,由 `_daily_archiver`
    在凌晨 GETDEL 取值后 UPSERT 到此表;Redis 仅保留 8 天滚动窗口,
    历史趋势完全依赖此表。
    """

    __tablename__ = "article_daily_views"

    # 北京时区日期(主键,一天一行)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
