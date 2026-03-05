"""Add amount column to prompts and change default status to quoted.

Revision ID: 004
Revises: 003
Create Date: 2026-03-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("prompts", sa.Column("amount", sa.Float, nullable=True))
    op.execute(
        "ALTER TABLE prompts ALTER COLUMN status SET DEFAULT 'quoted'"
    )


def downgrade() -> None:
    op.drop_column("prompts", "amount")
    op.execute(
        "ALTER TABLE prompts ALTER COLUMN status SET DEFAULT 'accepted'"
    )
