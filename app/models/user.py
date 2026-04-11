from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role in ('admin', 'manager', 'engineer')",
            name="ck_users_role_valid",
        ),
        Index("ix_users_role_is_active", "role", "is_active"),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)

    role = Column(String, nullable=False, default="engineer")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_orders = relationship(
        "Order",
        foreign_keys="Order.created_by",
        back_populates="creator",
    )
    assigned_orders = relationship(
        "Order",
        foreign_keys="Order.assigned_to",
        back_populates="assignee",
    )