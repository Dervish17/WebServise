from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


def _clean_required(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} не может быть пустым")
    return value


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class ClientCreate(BaseModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    notes: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _clean_required(value, "Название клиента")

    @field_validator("contact_person", "phone", "address", "notes", mode="before")
    @classmethod
    def clean_optional_fields(cls, value):
        return _clean_optional(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return None
        value = value.strip().lower()
        return value or None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_person: str | None
    phone: str | None
    email: EmailStr | None
    address: str | None
    notes: str | None
    created_at: datetime