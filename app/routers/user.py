from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.user_service import create_user

from app.db.session import get_db
from app.schemas.user import UserCreate
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/")
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user.email, user.password, user.role)

@router.get("/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()

