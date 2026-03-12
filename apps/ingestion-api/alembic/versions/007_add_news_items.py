"""Add news_items table for real-world news gap filling.

Revision ID: 007
Revises: 006
Create Date: 2026-03-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("edition_date", sa.String(10), nullable=False),
        sa.Column("category_id", sa.String(64), nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("snippet", sa.Text, nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("relevance_score", sa.Float, nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "source_url", "edition_date", name="uq_news_items_url_date"
        ),
    )
    op.create_index(
        "ix_news_items_edition_status",
        "news_items",
        ["edition_date", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_news_items_edition_status", table_name="news_items")
    op.drop_table("news_items")
