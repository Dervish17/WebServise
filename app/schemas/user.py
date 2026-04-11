from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    last_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    role: UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    last_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime