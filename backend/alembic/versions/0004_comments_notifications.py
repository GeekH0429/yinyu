"""comments, comment_likes, notifications + articles.comment_count

Revision ID: 0004_comments_notifications
Revises: 0003_daily_image
Create Date: 2026-07-23 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_comments_notifications"
down_revision: Union[str, None] = "0003_daily_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. articles 加 comment_count
    op.add_column(
        "articles",
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # 2. comments
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("reply_to_user_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reply_to_user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_comments_article_id", "comments", ["article_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index(
        "ix_comments_toplevel",
        "comments",
        ["article_id", "created_at"],
        postgresql_where=sa.text("parent_id IS NULL"),
    )
    op.create_index("ix_comments_parent", "comments", ["parent_id"])

    # 3. comment_likes
    op.create_table(
        "comment_likes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "comment_id", name="uq_comment_likes_user_comment"),
    )
    op.create_index("ix_comment_likes_user_id", "comment_likes", ["user_id"])
    op.create_index("ix_comment_likes_comment_id", "comment_likes", ["comment_id"])

    # 4. notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("comment_id", sa.Integer(), nullable=True),
        sa.Column("reply_comment_id", sa.Integer(), nullable=True),
        sa.Column(
            "is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("summary", sa.String(length=200), nullable=False, server_default=""),
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
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reply_comment_id"], ["comments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index(
        "ix_notifications_unread", "notifications", ["recipient_id", "is_read"]
    )
    op.create_index(
        "ix_notifications_recipient_created",
        "notifications",
        ["recipient_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_index("ix_notifications_unread", table_name="notifications")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_comment_likes_comment_id", table_name="comment_likes")
    op.drop_index("ix_comment_likes_user_id", table_name="comment_likes")
    op.drop_table("comment_likes")

    op.drop_index("ix_comments_parent", table_name="comments")
    op.drop_index("ix_comments_toplevel", table_name="comments")
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_article_id", table_name="comments")
    op.drop_table("comments")

    op.drop_column("articles", "comment_count")
