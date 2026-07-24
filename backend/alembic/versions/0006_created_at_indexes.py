"""created_at indexes for stats

Revision ID: 0006_created_at_indexes
Revises: 0005_articles_tags_gin
Create Date: 2026-07-25 00:00:00

为 users / articles / treeholes 的 created_at 加 BTree 索引,
加速管理后台 /stats/overview 的 `count() FILTER (WHERE created_at >= ?)`
与 /stats/trends 的 `WHERE created_at >= ? GROUP BY ...`。
此前三表均无 created_at 索引,聚合查询退化为 Seq Scan。
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006_created_at_indexes"
down_revision: Union[str, None] = "0005_articles_tags_gin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_articles_created_at", "articles", ["created_at"])
    op.create_index("ix_treeholes_created_at", "treeholes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_treeholes_created_at", table_name="treeholes")
    op.drop_index("ix_articles_created_at", table_name="articles")
    op.drop_index("ix_users_created_at", table_name="users")
