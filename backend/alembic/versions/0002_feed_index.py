"""feed index

Revision ID: 0002_feed_index
Revises: 0001_initial
Create Date: 2026-07-21 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_feed_index"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 部分索引:只为已发布文章建 (published_at, id),加速首页 feed 排序
    op.create_index(
        "ix_articles_feed",
        "articles",
        ["published_at", "id"],
        postgresql_where=sa.text("status = 'published'"),
    )


def downgrade() -> None:
    op.drop_index("ix_articles_feed", table_name="articles")
