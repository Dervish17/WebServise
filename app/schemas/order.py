from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import OrderStatus


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


class OrderCreate(BaseModel):
    title: str
    description: str | None = None
    equipment_id: int
    total_cost: Decimal | None = Field(default=None, ge=0)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _clean_required(value, "Название заявки")

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value):
        return _clean_optional(value)


class AssignOrderRequest(BaseModel):
    user_id: int


class ChangeStatusRequest(BaseModel):
    status: OrderStatus


class CreateCommentRequest(BaseModel):
    text: str

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _clean_required(value, "Комментарий")


class ClientShortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class EquipmentShortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    model: str | None
    serial_number: str | None
    manufacturer: str | None


class UserShortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: str
    total_cost: Decimal | None
    client_id: int
    equipment_id: int
    created_by: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime

    client: ClientShortResponse
    equipment: EquipmentShortResponse
    creator: UserShortResponse
    assignee: UserShortResponse | None