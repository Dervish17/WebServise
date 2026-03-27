from enum import Enum

class OrderStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"

class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    engineer = "engineer"