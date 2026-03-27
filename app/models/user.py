from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='engineer')

    created_at = Column(DateTime, default=datetime.utcnow)