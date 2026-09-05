"""时光胶囊模型:写给未来自己的信,封存到 unlock_at 才能开启。

设计要点:
    - 未到期:接口不回传 content(服务端强制),列表只见标题与开启日期。
    - 到期:App 内开启阅读;调度器(main.py _capsule_notifier)发邮件提醒。
    - notified_at:邮件发送认领标记(原子 UPDATE 置位),防止重复发送;
      NULL=未通知。邮件是 best-effort:认领后发送失败不重试(可接受)。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TimeCapsule(TimestampMixin, Base):
    __tablename__ = "time_capsules"
    __table_args__ = (
        # 调度器扫描:WHERE notified_at IS NULL AND unlock_at <= now
        Index("ix_time_capsules_unlock_at", "unlock_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 信件正文(纯文本,保留换行)。封存后不可修改、到期前不下发。
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 开启时间(带时区);存库统一 UTC
    unlock_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # 到期邮件认领标记
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
