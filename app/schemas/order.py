from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
    title: str
    description: str
    equipment_id: int


class AssignOrderRequest(BaseModel):
    user_id: int


class ChangeStatusRequest(BaseModel):
    status: OrderStatus


class CreateCommentRequest(BaseModel):
    text: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    client_id: int
    equipment_id: int
    created_by: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime