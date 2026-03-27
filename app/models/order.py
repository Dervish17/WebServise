from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db.database import Base
from app.core.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)

    title = Column(String)
    description = Column(String)
    status = Column(String, default=OrderStatus.new.value)

    client_id = Column(Integer, ForeignKey("clients.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))

    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)