from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from datetime import datetime
from app.db.database import Base


class OrderLog(Base):
    __tablename__ = "order_logs"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id"))

    action = Column(String)  # тип действия
    description = Column(Text)  # что произошло

    user_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)