"""Add world_ledger_history table for tracking ledger changes over time.

Revision ID: 011
Revises: 010
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "world_ledger_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ledger_json", sa.Text, nullable=False),
        sa.Column("edition_date", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_world_ledger_history_edition_date",
        "world_ledger_history",
        ["edition_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_world_ledger_history_edition_date",
        table_name="world_ledger_history",
    )
    op.drop_table("world_ledger_history")
