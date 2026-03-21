"""Add prompt_research_log table for tracking topic research queries and results.

Revision ID: 012
Revises: 011
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_research_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "prompt_id",
            sa.String(36),
            sa.ForeignKey("prompts.id"),
            nullable=False,
        ),
        sa.Column("edition_date", sa.String(10), nullable=False),
        sa.Column("queries_json", sa.Text, nullable=False),
        sa.Column("results_json", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="success",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_prompt_research_log_prompt_id",
        "prompt_research_log",
        ["prompt_id"],
    )
    op.create_index(
        "ix_prompt_research_log_edition_date",
        "prompt_research_log",
        ["edition_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prompt_research_log_edition_date",
        table_name="prompt_research_log",
    )
    op.drop_index(
        "ix_prompt_research_log_prompt_id",
        table_name="prompt_research_log",
    )
    op.drop_table("prompt_research_log")
