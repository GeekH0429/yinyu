"""warm_word_favorites table

Revision ID: 0010_warm_word_favorites
Revises: 0009_warm_words
Create Date: 2026-07-26 01:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_warm_word_favorites"
down_revision: Union[str, None] = "0009_warm_words"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "warm_word_favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("warm_word_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warm_word_id"], ["warm_words.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "warm_word_id", name="uq_warm_word_favorites_user_word"),
    )
    op.create_index("ix_warm_word_favorites_user_id", "warm_word_favorites", ["user_id"])
    op.create_index("ix_warm_word_favorites_warm_word_id", "warm_word_favorites", ["warm_word_id"])


def downgrade() -> None:
    op.drop_index("ix_warm_word_favorites_warm_word_id", table_name="warm_word_favorites")
    op.drop_index("ix_warm_word_favorites_user_id", table_name="warm_word_favorites")
    op.drop_table("warm_word_favorites")
