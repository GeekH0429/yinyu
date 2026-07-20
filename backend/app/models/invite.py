"""邀请码模型(注册时必须持有有效邀请码,保证封闭私密)。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class InviteCode(TimestampMixin, Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # 创建者(管理员);首个种子码可由系统初始化生成,created_by 为空
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    remark: Mapped[str | None] = mapped_column(String(120), nullable=True)

    max_uses: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def is_available(self) -> bool:
        import datetime as _dt

        return (
            self.is_active
            and self.used_count < self.max_uses
            and (self.expires_at is None or self.expires_at > _dt.datetime.now(_dt.timezone.utc))
        )
