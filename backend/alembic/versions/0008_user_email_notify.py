"""user.email_notify_enabled

Revision ID: 0008_user_email_notify
Revises: 0007_article_daily_views
Create Date: 2026-07-25 00:00:00

Add users.email_notify_enabled boolean column (default false).
Users opt in via PUT /api/v1/me to receive email notifications when
someone comments on their article, replies to their comment, or @mentions them.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_user_email_notify"
down_revision: Union[str, None] = "0007_article_daily_views"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_notify_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "email_notify_enabled")
