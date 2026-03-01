"""Initial schema — prompts, categorised_prompts, payment_refs, editions,
edition_articles.

Revision ID: 001
Revises:
Create Date: 2026-03-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("payment_ref", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="accepted"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "categorised_prompts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "prompt_id",
            sa.String(36),
            sa.ForeignKey("prompts.id"),
            nullable=False,
        ),
        sa.Column("category_id", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "payment_refs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "braintree_transaction_id", sa.String(255), nullable=False, unique=True
        ),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="settled"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "editions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "edition_articles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "edition_id",
            sa.String(36),
            sa.ForeignKey("editions.id"),
            nullable=False,
        ),
        sa.Column("newspaper_id", sa.String(64), nullable=False),
        sa.Column("content_json", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("edition_articles")
    op.drop_table("editions")
    op.drop_table("payment_refs")
    op.drop_table("categorised_prompts")
    op.drop_table("prompts")
