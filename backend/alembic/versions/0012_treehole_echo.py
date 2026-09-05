"""treehole echo: treeholes.echo_count + notifications.treehole_id + treehole_echoes

Revision ID: 0012_treehole_echo
Revises: 0011_article_schedule_and_notify
Create Date: 2026-09-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_treehole_echo"
down_revision: Union[str, None] = "0011_article_schedule_and_notify"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 树洞反范式回音计数
    op.add_column(
        "treeholes",
        sa.Column("echo_count", sa.Integer(), nullable=False, server_default="0"),
    )
    # 通知可指向树洞(仅 treehole_echo 类型)
    op.add_column("notifications", sa.Column("treehole_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_notifications_treehole_id_treeholes",
        "notifications",
        "treeholes",
        ["treehole_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # 回音表:一人一洞一枚
    op.create_table(
        "treehole_echoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("treehole_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["treehole_id"], ["treeholes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("treehole_id", "user_id", name="uq_treehole_echoes_treehole_user"),
    )
    op.create_index("ix_treehole_echoes_treehole_id", "treehole_echoes", ["treehole_id"])
    op.create_index("ix_treehole_echoes_user_id", "treehole_echoes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_treehole_echoes_user_id", table_name="treehole_echoes")
    op.drop_index("ix_treehole_echoes_treehole_id", table_name="treehole_echoes")
    op.drop_table("treehole_echoes")
    op.drop_constraint(
        "fk_notifications_treehole_id_treeholes", "notifications", type_="foreignkey"
    )
    op.drop_column("notifications", "treehole_id")
    op.drop_column("treeholes", "echo_count")
