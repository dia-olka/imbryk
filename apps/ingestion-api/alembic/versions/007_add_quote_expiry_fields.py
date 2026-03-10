"""Add checkout_attempts to prompts for quote expiry enforcement.

Revision ID: 007
Revises: 006
Create Date: 2026-03-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prompts",
        sa.Column(
            "checkout_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    with op.batch_alter_table("prompts") as batch_op:
        batch_op.drop_column("checkout_attempts")
