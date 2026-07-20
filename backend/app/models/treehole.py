"""树洞模型。

核心特性:
    - 无列表、无标签、全量隐匿;仅凭 6 位数字暗号解锁单篇。
    - code 全局唯一;默认系统生成,可刷新,可自定义。
    - 暗号读者读不到 author_id(接口层不回传作者信息)。
"""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

CODE_LENGTH = 6


class TreeHole(TimestampMixin, Base):
    __tablename__ = "treeholes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 仅作者本人 / 管理员可在"我的"里看到自己写的;暗号读者看不到
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content_html: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 6 位数字暗号,全局唯一
    code: Mapped[str] = mapped_column(String(CODE_LENGTH), unique=True, index=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
