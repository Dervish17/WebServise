from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
    title: str
    description: str
    equipment_id: int
    total_cost: Decimal | None = None


class AssignOrderRequest(BaseModel):
    user_id: int


class ChangeStatusRequest(BaseModel):
    status: OrderStatus


class CreateCommentRequest(BaseModel):
    text: str


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
    description: str
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