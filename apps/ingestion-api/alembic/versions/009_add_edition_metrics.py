"""Add edition_metrics table for Cloudflare reader analytics.

Revision ID: 009
Revises: 008
Create Date: 2026-03-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "edition_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("edition_date", sa.String(10), nullable=False),
        sa.Column("newspaper_id", sa.String(64), nullable=False),
        sa.Column("article_slug", sa.String(255), nullable=False),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("page_views", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "edition_date",
            "newspaper_id",
            "article_slug",
            name="uq_edition_metrics_date_paper_slug",
        ),
    )
    op.create_index(
        "ix_edition_metrics_edition_date",
        "edition_metrics",
        ["edition_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_edition_metrics_edition_date",
        table_name="edition_metrics",
    )
    op.drop_table("edition_metrics")
