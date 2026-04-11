"""harden constraints and indexes

Revision ID: 9e4b7d5b9f1a
Revises: c189836bb27f
Create Date: 2026-04-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9e4b7d5b9f1a"
down_revision: Union[str, Sequence[str], None] = "55eb52231764"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "role", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "created_at", existing_type=sa.DateTime(), nullable=False)
    op.create_check_constraint(
        "ck_users_role_valid",
        "users",
        "role in ('admin', 'manager', 'engineer')",
    )
    op.create_index("ix_users_role_is_active", "users", ["role", "is_active"], unique=False)

    op.alter_column("clients", "name", existing_type=sa.String(), nullable=False)
    op.alter_column("clients", "created_at", existing_type=sa.DateTime(), nullable=False)
    op.create_index("ix_clients_name", "clients", ["name"], unique=False)
    op.create_index("ix_clients_email", "clients", ["email"], unique=False)
    op.create_index("ix_clients_created_at", "clients", ["created_at"], unique=False)

    op.alter_column("equipment", "client_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("equipment", "name", existing_type=sa.String(), nullable=False)
    op.alter_column("equipment", "created_at", existing_type=sa.DateTime(), nullable=False)
    op.create_index("ix_equipment_client_id", "equipment", ["client_id"], unique=False)
    op.create_index("ix_equipment_name", "equipment", ["name"], unique=False)
    op.create_index("ix_equipment_serial_number", "equipment", ["serial_number"], unique=False)
    op.create_index("ix_equipment_created_at", "equipment", ["created_at"], unique=False)

    op.alter_column("orders", "title", existing_type=sa.String(), nullable=False)
    op.alter_column("orders", "status", existing_type=sa.String(), nullable=False)
    op.alter_column("orders", "client_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("orders", "equipment_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("orders", "created_by", existing_type=sa.Integer(), nullable=False)
    op.alter_column("orders", "created_at", existing_type=sa.DateTime(), nullable=False)
    op.alter_column("orders", "updated_at", existing_type=sa.DateTime(), nullable=False)
    op.create_check_constraint(
        "ck_orders_status_valid",
        "orders",
        "status in ('new', 'in_progress', 'done')",
    )
    op.create_check_constraint(
        "ck_orders_total_cost_non_negative",
        "orders",
        "total_cost is null or total_cost >= 0",
    )
    op.create_index("ix_orders_status", "orders", ["status"], unique=False)
    op.create_index("ix_orders_created_at", "orders", ["created_at"], unique=False)
    op.create_index("ix_orders_client_id", "orders", ["client_id"], unique=False)
    op.create_index("ix_orders_equipment_id", "orders", ["equipment_id"], unique=False)
    op.create_index("ix_orders_created_by", "orders", ["created_by"], unique=False)
    op.create_index("ix_orders_assigned_to", "orders", ["assigned_to"], unique=False)
    op.create_index("ix_orders_client_status", "orders", ["client_id", "status"], unique=False)
    op.create_index("ix_orders_assigned_to_status", "orders", ["assigned_to", "status"], unique=False)

    op.alter_column("order_logs", "order_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("order_logs", "action", existing_type=sa.String(), nullable=False)
    op.alter_column("order_logs", "description", existing_type=sa.Text(), nullable=False)
    op.alter_column("order_logs", "user_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("order_logs", "created_at", existing_type=sa.DateTime(), nullable=False)
    op.create_index("ix_order_logs_order_id", "order_logs", ["order_id"], unique=False)
    op.create_index("ix_order_logs_user_id", "order_logs", ["user_id"], unique=False)
    op.create_index("ix_order_logs_action", "order_logs", ["action"], unique=False)
    op.create_index("ix_order_logs_created_at", "order_logs", ["created_at"], unique=False)

    op.alter_column("status_history", "order_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("status_history", "old_status", existing_type=sa.String(), nullable=False)
    op.alter_column("status_history", "new_status", existing_type=sa.String(), nullable=False)
    op.alter_column("status_history", "changed_by", existing_type=sa.Integer(), nullable=False)
    op.alter_column("status_history", "changed_at", existing_type=sa.DateTime(), nullable=False)
    op.create_index("ix_status_history_order_id", "status_history", ["order_id"], unique=False)
    op.create_index("ix_status_history_changed_by", "status_history", ["changed_by"], unique=False)
    op.create_index("ix_status_history_changed_at", "status_history", ["changed_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_status_history_changed_at", table_name="status_history")
    op.drop_index("ix_status_history_changed_by", table_name="status_history")
    op.drop_index("ix_status_history_order_id", table_name="status_history")
    op.alter_column("status_history", "changed_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("status_history", "changed_by", existing_type=sa.Integer(), nullable=True)
    op.alter_column("status_history", "new_status", existing_type=sa.String(), nullable=True)
    op.alter_column("status_history", "old_status", existing_type=sa.String(), nullable=True)
    op.alter_column("status_history", "order_id", existing_type=sa.Integer(), nullable=True)

    op.drop_index("ix_order_logs_created_at", table_name="order_logs")
    op.drop_index("ix_order_logs_action", table_name="order_logs")
    op.drop_index("ix_order_logs_user_id", table_name="order_logs")
    op.drop_index("ix_order_logs_order_id", table_name="order_logs")
    op.alter_column("order_logs", "created_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("order_logs", "user_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("order_logs", "description", existing_type=sa.Text(), nullable=True)
    op.alter_column("order_logs", "action", existing_type=sa.String(), nullable=True)
    op.alter_column("order_logs", "order_id", existing_type=sa.Integer(), nullable=True)

    op.drop_index("ix_orders_assigned_to_status", table_name="orders")
    op.drop_index("ix_orders_client_status", table_name="orders")
    op.drop_index("ix_orders_assigned_to", table_name="orders")
    op.drop_index("ix_orders_created_by", table_name="orders")
    op.drop_index("ix_orders_equipment_id", table_name="orders")
    op.drop_index("ix_orders_client_id", table_name="orders")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_constraint("ck_orders_total_cost_non_negative", "orders", type_="check")
    op.drop_constraint("ck_orders_status_valid", "orders", type_="check")
    op.alter_column("orders", "updated_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("orders", "created_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("orders", "created_by", existing_type=sa.Integer(), nullable=True)
    op.alter_column("orders", "equipment_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("orders", "client_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("orders", "status", existing_type=sa.String(), nullable=True)
    op.alter_column("orders", "title", existing_type=sa.String(), nullable=True)

    op.drop_index("ix_equipment_created_at", table_name="equipment")
    op.drop_index("ix_equipment_serial_number", table_name="equipment")
    op.drop_index("ix_equipment_name", table_name="equipment")
    op.drop_index("ix_equipment_client_id", table_name="equipment")
    op.alter_column("equipment", "created_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("equipment", "name", existing_type=sa.String(), nullable=True)
    op.alter_column("equipment", "client_id", existing_type=sa.Integer(), nullable=True)

    op.drop_index("ix_clients_created_at", table_name="clients")
    op.drop_index("ix_clients_email", table_name="clients")
    op.drop_index("ix_clients_name", table_name="clients")
    op.alter_column("clients", "created_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("clients", "name", existing_type=sa.String(), nullable=True)

    op.drop_index("ix_users_role_is_active", table_name="users")
    op.drop_constraint("ck_users_role_valid", "users", type_="check")
    op.alter_column("users", "created_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("users", "role", existing_type=sa.String(), nullable=True)