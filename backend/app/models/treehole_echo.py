"""树洞回音模型。

设计要点:
    - 读者解锁树洞后可留一枚匿名回音(仅限预设短句,杜绝骚扰与身份推理)。
    - user×treehole 唯一:一人一洞一枚,可改不可刷。
    - 读者身份仅用于唯一约束与限流;任何读者侧接口都不回传 user 信息。
"""
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TreeHoleEcho(TimestampMixin, Base):
    __tablename__ = "treehole_echoes"
    __table_args__ = (
        UniqueConstraint("treehole_id", "user_id", name="uq_treehole_echoes_treehole_user"),
        Index("ix_treehole_echoes_treehole_id", "treehole_id"),
        Index("ix_treehole_echoes_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    treehole_id: Mapped[int] = mapped_column(
        ForeignKey("treeholes.id", ondelete="CASCADE"), nullable=False
    )
    # 回音者:仅用于"一人一枚"去重;不出现在任何读者/作者展示接口
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 预设短句(服务端白名单校验,见 services/treehole_echo.py 的 ECHO_PRESETS)
    message: Mapped[str] = mapped_column(String(30), nullable=False)
