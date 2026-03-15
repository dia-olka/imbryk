"""Add marketing_posts table for autonomous social media promotion.

Revision ID: 010
Revises: 009
Create Date: 2026-03-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marketing_posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("edition_date", sa.String(10), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("post_type", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("post_url", sa.Text, nullable=True),
        sa.Column("post_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="posted"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_marketing_posts_edition_date",
        "marketing_posts",
        ["edition_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_marketing_posts_edition_date",
        table_name="marketing_posts",
    )
    op.drop_table("marketing_posts")
