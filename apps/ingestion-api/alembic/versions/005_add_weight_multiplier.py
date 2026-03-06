"""Add weight_multiplier column to prompts table.

Revision ID: 005
Revises: 004
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prompts",
        sa.Column(
            "weight_multiplier",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    op.drop_column("prompts", "weight_multiplier")
