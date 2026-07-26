"""暖话收藏:用户 × 暖话 唯一,记录收藏时间。"""
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WarmWordFavorite(TimestampMixin, Base):
    __tablename__ = "warm_word_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "warm_word_id", name="uq_warm_word_favorites_user_word"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    warm_word_id: Mapped[int] = mapped_column(
        ForeignKey("warm_words.id", ondelete="CASCADE"), index=True, nullable=False
    )
