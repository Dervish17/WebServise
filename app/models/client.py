from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        Index("ix_clients_name", "name"),
        Index("ix_clients_email", "email"),
        Index("ix_clients_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    equipments = relationship("Equipment", back_populates="client")
    orders = relationship("Order", back_populates="client")