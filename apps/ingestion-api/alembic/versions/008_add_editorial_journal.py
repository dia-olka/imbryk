"""Add editorial_journal table for persistent per-persona editorial memory.

Revision ID: 008
Revises: 007
Create Date: 2026-03-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "editorial_journal",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("persona_id", sa.String(64), nullable=False),
        sa.Column("entry_date", sa.String(10), nullable=False),
        sa.Column("entry_type", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "persona_id",
            "entry_date",
            "entry_type",
            name="uq_editorial_journal_persona_date_type",
        ),
    )
    op.create_index(
        "ix_editorial_journal_persona_date",
        "editorial_journal",
        ["persona_id", "entry_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_editorial_journal_persona_date",
        table_name="editorial_journal",
    )
    op.drop_table("editorial_journal")
