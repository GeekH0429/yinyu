"""article scheduled publish + user article notify

Revision ID: 0011_article_schedule_and_notify
Revises: 0010_warm_word_favorites
Create Date: 2026-08-20 00:00:00

Add articles.scheduled_at timestamptz column plus a partial index for the
background publisher scan (WHERE status = 'scheduled'), and add
users.article_notify_enabled boolean (default false) for opting in to
"new article published" email digests.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_article_schedule_and_notify"
down_revision: Union[str, None] = "0010_warm_word_favorites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_articles_scheduled",
        "articles",
        ["scheduled_at"],
        postgresql_where=sa.text("status = 'scheduled'"),
    )
    op.add_column(
        "users",
        sa.Column(
            "article_notify_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "article_notify_enabled")
    op.drop_index("ix_articles_scheduled", table_name="articles")
    op.drop_column("articles", "scheduled_at")
