"""add notes to clients

Revision ID: c97ae08bdb1c
Revises: ee402f2caf39
Create Date: 2026-03-27 16:26:30.211567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c97ae08bdb1c'
down_revision: Union[str, Sequence[str], None] = 'ee402f2caf39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('notes', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_status_history_order_id_orders',
        'status_history',
        'orders',
        ['order_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_status_history_order_id_orders',
        'status_history',
        type_='foreignkey',
    )
    op.drop_column('clients', 'notes')