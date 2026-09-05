"""excerpts table

Revision ID: 0014_excerpts
Revises: 0013_time_capsule
Create Date: 2026-09-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_excerpts"
down_revision: Union[str, None] = "0013_time_capsule"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "excerpts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("article_title", sa.String(200), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_excerpts_user_created", "excerpts", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_excerpts_user_created", table_name="excerpts")
    op.drop_table("excerpts")
