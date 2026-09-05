"""摘抄模型:阅读时收藏的句子。

设计要点:
    - article_id 故意不做外键级联 —— 摘抄是用户的笔记本,文章被删摘抄仍要保留;
      因此同时冗余 article_title 快照,卡片/列表展示不再回查文章。
    - content 为纯文本句子(≤500 字),来源是 mp-html 选区或手动输入,存前已剥标签。
"""
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Excerpt(TimestampMixin, Base):
    __tablename__ = "excerpts"
    __table_args__ = (
        # 列表热路径:WHERE user_id=? ORDER BY created_at DESC
        Index("ix_excerpts_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 原文章 id(仅作溯源跳转;文章可能已删,不做外键)
    article_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 文章标题快照:列表/卡片展示不再回查
    article_title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    # 句子本身(纯文本)
    content: Mapped[str] = mapped_column(Text, nullable=False)
