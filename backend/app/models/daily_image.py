"""每日一图模型(管理员排期,用户端每日全屏弹层 + 历史回溯)。"""
from datetime import date

from sqlalchemy import Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DailyImage(TimestampMixin, Base):
    __tablename__ = "daily_images"
    __table_args__ = (
        # 同一天仅允许一张
        UniqueConstraint("publish_date", name="uq_daily_images_publish_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # 排期日期,不带时区;查询「今天」时服务端按北京时间构造 date
    publish_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # 复用 /uploads 接口返回的相对路径(/uploads/YYYY/MM/DD/xxx.webp)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
