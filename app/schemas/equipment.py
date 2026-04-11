from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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


class EquipmentCreate(BaseModel):
    name: str
    model: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    client_id: int

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _clean_required(value, "Название оборудования")

    @field_validator("model", "manufacturer", mode="before")
    @classmethod
    def clean_optional_fields(cls, value):
        return _clean_optional(value)

    @field_validator("serial_number", mode="before")
    @classmethod
    def normalize_serial_number(cls, value):
        if value is None:
            return None
        value = value.strip().upper()
        return value or None


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    model: str | None
    serial_number: str | None
    manufacturer: str | None
    client_id: int
    created_at: datetime