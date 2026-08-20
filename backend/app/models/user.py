"""用户模型。

角色:
    - ROLE_USER  普通用户(可发布图文 / 树洞)
    - ROLE_ADMIN 管理员(可管理全部内容 + 后台)
"""
from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

ROLE_USER = "user"
ROLE_ADMIN = "admin"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # stats 趋势/概览热路径:WHERE created_at >= ? / GROUP BY created_at
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    nickname: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False, default=ROLE_USER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 是否在「被评论 / 被回复 / 被 @提及」时发送邮件提醒。
    # 收件邮箱取 self.email;为空则不发。
    email_notify_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # 是否订阅「新文章发布」邮件推送(独立于上面的互动提醒)。
    article_notify_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN
