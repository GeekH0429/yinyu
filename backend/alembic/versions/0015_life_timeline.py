"""life timeline: user birthday/lifespan + life_milestones

Revision ID: 0015_life_timeline
Revises: 0014_excerpts
Create Date: 2026-09-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "0015_life_timeline"
down_revision: Union[str, None] = "0014_excerpts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("birthday", sa.Date(), nullable=True))
    op.add_column(
        "users",
        sa.Column("lifespan_years", sa.Integer(), nullable=False, server_default="80"),
    )
    op.create_table(
        "life_milestones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(40), nullable=False),
        sa.Column("color", sa.String(9), nullable=False, server_default="#C4A882"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("site", sa.String(60), nullable=True),
        sa.Column("images", ARRAY(sa.String(500)), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_life_milestones_user_start", "life_milestones", ["user_id", "start_date"])


def downgrade() -> None:
    op.drop_index("ix_life_milestones_user_start", table_name="life_milestones")
    op.drop_table("life_milestones")
    op.drop_column("users", "lifespan_years")
    op.drop_column("users", "birthday")
