"""articles tags GIN index

Revision ID: 0005_articles_tags_gin
Revises: 0004_comments_notifications
Create Date: 2026-07-23 00:00:00

为 articles.tags(ARRAY)添加 GIN 索引,加速 `value = ANY(tags)` 标签筛选。
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005_articles_tags_gin"
down_revision: Union[str, None] = "0004_comments_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_articles_tags_gin",
        "articles",
        ["tags"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_articles_tags_gin", table_name="articles")
