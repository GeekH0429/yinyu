"""time_capsules table

Revision ID: 0013_time_capsule
Revises: 0012_treehole_echo
Create Date: 2026-09-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_time_capsule"
down_revision: Union[str, None] = "0012_treehole_echo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "time_capsules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("unlock_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_time_capsules_user_id", "time_capsules", ["user_id"])
    op.create_index("ix_time_capsules_unlock_at", "time_capsules", ["unlock_at"])


def downgrade() -> None:
    op.drop_index("ix_time_capsules_unlock_at", table_name="time_capsules")
    op.drop_index("ix_time_capsules_user_id", table_name="time_capsules")
    op.drop_table("time_capsules")
