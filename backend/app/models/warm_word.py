"""暖话模型:按场景分组的治愈短句,登录用户每日随机抽取。"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WarmWord(TimestampMixin, Base):
    __tablename__ = "warm_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    scene: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
