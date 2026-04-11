from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        Index("ix_equipment_client_id", "client_id"),
        Index("ix_equipment_name", "name"),
        Index("ix_equipment_serial_number", "serial_number"),
        Index("ix_equipment_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    name = Column(String, nullable=False)
    model = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    client = relationship("Client", back_populates="equipments")
    orders = relationship("Order", back_populates="equipment")