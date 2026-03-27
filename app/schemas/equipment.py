from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EquipmentCreate(BaseModel):
    name: str
    model: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    client_id: int


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    model: str | None
    serial_number: str | None
    manufacturer: str | None
    client_id: int
    created_at: datetime