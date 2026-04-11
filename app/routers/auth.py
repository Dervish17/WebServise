from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import TokenResponse
from app.services.auth_service import login_user
from app.core.login_rate_limit import (
    clear_login_failures,
    ensure_login_allowed,
    record_failed_login,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    email = form_data.username

    ensure_login_allowed(client_ip, email)

    token = login_user(db, email, form_data.password)

    if not token:
        record_failed_login(client_ip, email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    clear_login_failures(client_ip, email)

    return {
        "access_token": token,
        "token_type": "bearer",
    }