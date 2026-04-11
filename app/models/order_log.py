from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class OrderLog(Base):
    __tablename__ = "order_logs"
    __table_args__ = (
        Index("ix_order_logs_order_id", "order_id"),
        Index("ix_order_logs_user_id", "user_id"),
        Index("ix_order_logs_action", "action"),
        Index("ix_order_logs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    action = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="logs")