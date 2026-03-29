from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime

from sqlalchemy.orm import relationship

from app.db.database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))

    name = Column(String)
    model = Column(String)
    serial_number = Column(String)
    manufacturer = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="equipments")
    orders = relationship("Order", back_populates="equipment")