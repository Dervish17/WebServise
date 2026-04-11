"""expand order statuses

Revision ID: 4b72a9c13e41
Revises: 9e4b7d5b9f1a
Create Date: 2026-04-11 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "4b72a9c13e41"
down_revision: Union[str, Sequence[str], None] = "9e4b7d5b9f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_orders_status_valid", "orders", type_="check")
    op.create_check_constraint(
        "ck_orders_status_valid",
        "orders",
        "status in ('new', 'diagnostics', 'estimate_approved', 'in_progress', 'done', 'awaiting_payment', 'closed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_orders_status_valid", "orders", type_="check")
    op.create_check_constraint(
        "ck_orders_status_valid",
        "orders",
        "status in ('new', 'in_progress', 'done')",
    )