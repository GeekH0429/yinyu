"""warm_words table

Revision ID: 0009_warm_words
Revises: 0008_user_email_notify
Create Date: 2026-07-26 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_warm_words"
down_revision: Union[str, None] = "0008_user_email_notify"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "warm_words",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scene", sa.String(length=40), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
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
    )
    op.create_index("ix_warm_words_scene", "warm_words", ["scene"])


def downgrade() -> None:
    op.drop_index("ix_warm_words_scene", table_name="warm_words")
    op.drop_table("warm_words")
