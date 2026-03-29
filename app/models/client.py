from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from sqlalchemy.orm import relationship

from app.db.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    equipments = relationship("Equipment", back_populates="client")
    orders = relationship("Order", back_populates="client")