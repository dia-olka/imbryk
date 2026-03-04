"""Add image_url column to edition_articles.

Revision ID: 003
Revises: 002
Create Date: 2026-03-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "edition_articles",
        sa.Column("image_url", sa.String(512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("edition_articles", "image_url")
