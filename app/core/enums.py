from enum import Enum


class OrderStatus(str, Enum):
    new = "new"
    diagnostics = "diagnostics"
    estimate_approved = "estimate_approved"
    in_progress = "in_progress"
    done = "done"
    awaiting_payment = "awaiting_payment"
    closed = "closed"


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    engineer = "engineer"