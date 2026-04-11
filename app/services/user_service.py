from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password, verify_password
from app.models.order import Order
from app.models.order_log import OrderLog
from app.models.status_history import StatusHistory
from app.models.user import User


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_role(role: str) -> str:
    allowed_roles = {item.value for item in UserRole}
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимая роль пользователя",
        )
    return role


def create_user(
    db: Session,
    email: str,
    password: str,
    role: str,
    last_name: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
) -> User:
    email = _normalize_email(email)
    role = _validate_role(role)

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен быть не короче 6 символов",
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    user = User(
        email=email,
        hashed_password=hash_password(password),
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    user_id: int,
    email: str,
    role: str,
    last_name: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
) -> User:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise ValueError("User not found")

    email = _normalize_email(email)
    role = _validate_role(role)

    existing_user = (
        db.query(User)
        .filter(User.email == email, User.id != user_id)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    user.email = email
    user.role = role
    user.last_name = last_name
    user.first_name = first_name
    user.middle_name = middle_name

    db.commit()
    db.refresh(user)

    return user


def delete_user(
    db: Session,
    user_id: int,
    current_user_id: int,
) -> None:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя",
        )

    created_order = db.query(Order).filter(Order.created_by == user.id).first()
    if created_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить пользователя: он создавал заявки",
        )

    assigned_order = db.query(Order).filter(Order.assigned_to == user.id).first()
    if assigned_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить пользователя: он назначен на заявки",
        )

    order_log = db.query(OrderLog).filter(OrderLog.user_id == user.id).first()
    if order_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить пользователя: у него есть записи в истории действий",
        )

    status_history = db.query(StatusHistory).filter(StatusHistory.changed_by == user.id).first()
    if status_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить пользователя: у него есть история смены статусов",
        )

    db.delete(user)
    db.commit()


def toggle_user_active(
    db: Session,
    user_id: int,
    current_user_id: int,
) -> User:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать самого себя",
        )

    user.is_active = not user.is_active

    db.commit()
    db.refresh(user)

    return user


def change_user_password(
    db: Session,
    user_id: int,
    current_password: str,
    new_password: str,
) -> None:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущий пароль введён неверно",
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен быть не короче 6 символов",
        )

    user.hashed_password = hash_password(new_password)

    db.commit()


def update_profile(
    db: Session,
    user_id: int,
    email: str,
    last_name: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
) -> tuple[User, bool]:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    email = _normalize_email(email)

    existing_user = (
        db.query(User)
        .filter(User.email == email, User.id != user_id)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    old_email = user.email

    user.email = email
    user.last_name = last_name
    user.first_name = first_name
    user.middle_name = middle_name

    db.commit()
    db.refresh(user)

    email_changed = old_email != user.email
    return user, email_changed