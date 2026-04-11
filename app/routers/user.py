from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user

router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user: UserCreate,
    db: DbSession,
    _admin: Annotated[User, Depends(require_roles(UserRole.admin))],
):
    return create_user(
        db=db,
        email=user.email,
        password=user.password,
        role=user.role,
        last_name=user.last_name,
        first_name=user.first_name,
        middle_name=user.middle_name,
    )


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: DbSession,
    _admin: Annotated[User, Depends(require_roles(UserRole.admin))],
):
    return db.query(User).all()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: DbSession,
    _admin: Annotated[User, Depends(require_roles(UserRole.admin))],
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user