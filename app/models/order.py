from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from datetime import datetime

from sqlalchemy.orm import relationship

from app.db.database import Base
from app.core.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)

    title = Column(String)
    description = Column(String)
    status = Column(String, default=OrderStatus.new.value)
    total_cost = Column(Numeric(10,2), nullable=True)

    client_id = Column(Integer, ForeignKey("clients.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))

    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="orders")
    equipment = relationship("Equipment", back_populates="orders")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_orders")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_orders")
    logs = relationship("OrderLog", back_populates="order")
    status_history = relationship("StatusHistory", back_populates="order")