from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import ALGORITHM, SECRET_KEY
from app.db.session import get_db
from app.models.user import User

templates = Jinja2Templates(directory="app/templates")


def render_alert(
    request: Request, text: str, kind: str = "success", status_code: int = 200
):
    return templates.TemplateResponse(
        request,
        "shared/_alert.html",
        {
            "text": text,
            "kind": kind,
        },
        status_code=status_code,
    )


def get_current_ui_user(
    ui_user_email: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not ui_user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = db.query(User).filter(User.email == ui_user_email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_user_from_token_value(token: str | None, db: Session) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        return None

    if not email:
        return None

    user = db.query(User).filter(User.email == email).first()
    return user


def get_ui_user(db: Session) -> User:
    user = db.query(User).order_by(User.id.asc()).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found for UI actions",
        )

    return user
