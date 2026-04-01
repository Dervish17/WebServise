from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, create_access_token


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def login_user(db: Session, email: str, password: str):
    user = authenticate_user(db, email, password)

    if not user:
        return None

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return token