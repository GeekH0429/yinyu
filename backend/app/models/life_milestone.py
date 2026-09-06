"""人生节点模型:「人生时光轴」上的自定义人生阶段。

设计要点:
    - 纯个人私密数据:无他人可见入口、无列表接口(与树洞/胶囊同一隐匿理念)。
    - 默认学制节点(童年/幼儿园/小学/初中/高中/大学)不入库 —— 它们是生日的
      纯函数,由 App 端按生日 + 9 月入学规则推算;只有用户创建/编辑过的节点落库。
      这样修改生日时零成本重算,无需删库重建。
    - images 为节点相册(上传接口返回的 URL 列表,JSON 数组),可为空。
"""
from datetime import date

from sqlalchemy import ARRAY, Date, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LifeMilestone(TimestampMixin, Base):
    __tablename__ = "life_milestones"
    __table_args__ = (
        # 时光轴加载热路径:WHERE user_id=? ORDER BY start_date
        Index("ix_life_milestones_user_start", "user_id", "start_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 节点名称(如「初中」「在杭州的日子」)
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    # 节点颜色(十六进制,如 #C77BAA;暖色系色板由 App 端预置)
    color: Mapped[str] = mapped_column(String(9), nullable=False, default="#C4A882")
    # 起止日期(含端点;格子按该区间着色)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    # 地点(可选,如「杭州」)
    site: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # 节点相册:上传 URL 列表
    images: Mapped[list[str]] = mapped_column(ARRAY(String(500)), nullable=False, default=list)
