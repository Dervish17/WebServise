from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db.database import Base


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id"))
    old_status = Column(String)
    new_status = Column(String)

    changed_by = Column(Integer, ForeignKey("users.id"))

    changed_at = Column(DateTime, default=datetime.utcnow)