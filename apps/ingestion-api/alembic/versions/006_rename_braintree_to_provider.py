"""Rename braintree_transaction_id to provider_transaction_id.

Revision ID: 006
Revises: 005
Create Date: 2026-03-06
"""

from typing import Sequence, Union

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("payment_refs") as batch_op:
        batch_op.alter_column(
            "braintree_transaction_id",
            new_column_name="provider_transaction_id",
        )


def downgrade() -> None:
    with op.batch_alter_table("payment_refs") as batch_op:
        batch_op.alter_column(
            "provider_transaction_id",
            new_column_name="braintree_transaction_id",
        )
