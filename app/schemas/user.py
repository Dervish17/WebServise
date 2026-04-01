from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    last_name: str | None
    first_name: str | None
    middle_name: str | None
    role: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    last_name: str | None
    first_name: str | None
    middle_name: str | None
    role: str
    is_active: bool
    created_at: datetime