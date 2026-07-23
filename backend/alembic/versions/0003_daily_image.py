"""daily image table

Revision ID: 0003_daily_image
Revises: 0002_feed_index
Create Date: 2026-07-23 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_daily_image"
down_revision: Union[str, None] = "0002_feed_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("publish_date", sa.Date(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("publish_date", name="uq_daily_images_publish_date"),
    )
    op.create_index(
        "ix_daily_images_publish_date", "daily_images", ["publish_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_daily_images_publish_date", table_name="daily_images")
    op.drop_table("daily_images")
