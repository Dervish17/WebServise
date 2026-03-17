from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db.database import Base


class OrderLog(Base):
    __tablename__ = "order_logs"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    message = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)