"""article_daily_views archive table

Revision ID: 0007_article_daily_views
Revises: 0006_created_at_indexes
Create Date: 2026-07-25 00:00:00

新建 article_daily_views 表,持久化按日文章浏览量。
数据源是 Redis `view:daily:article:{YYYYMMDD}`,由后台 _daily_archiver
在凌晨 01:00 (CN_TZ) 左右 GETDEL 取值后 UPSERT 到此表。
Redis 仅保留 8 天滚动窗口,历史趋势完全依赖此表。

不回填历史数据:articles.view_count 是累计值,无法回推到每日,
明确"按日统计从本表上线日开始,之前显示为 0"。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_article_daily_views"
down_revision: Union[str, None] = "0006_created_at_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_daily_views",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("date", name=op.f("pk_article_daily_views")),
    )


def downgrade() -> None:
    op.drop_table("article_daily_views")
