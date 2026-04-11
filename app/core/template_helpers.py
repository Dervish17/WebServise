from app.models.user import User


def has_role(user: User | None, *roles: str) -> bool:
    return bool(user and user.role in roles)


def is_admin(user: User | None) -> bool:
    return has_role(user, "admin")


def can_manage(user: User | None) -> bool:
    return has_role(user, "admin", "manager")