from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.enums import OrderStatus
from app.db.database import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status in ('new', 'in_progress', 'done')",
            name="ck_orders_status_valid",
        ),
        CheckConstraint(
            "total_cost is null or total_cost >= 0",
            name="ck_orders_total_cost_non_negative",
        ),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_client_id", "client_id"),
        Index("ix_orders_equipment_id", "equipment_id"),
        Index("ix_orders_created_by", "created_by"),
        Index("ix_orders_assigned_to", "assigned_to"),
        Index("ix_orders_client_status", "client_id", "status"),
        Index("ix_orders_assigned_to_status", "assigned_to", "status"),
    )

    id = Column(Integer, primary_key=True)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default=OrderStatus.new.value, nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=True)

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    client = relationship("Client", back_populates="orders")
    equipment = relationship("Equipment", back_populates="orders")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_orders")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_orders")
    logs = relationship("OrderLog", back_populates="order")
    status_history = relationship("StatusHistory", back_populates="order")