from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ClientCreate(BaseModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_person: str | None
    phone: str | None
    email: EmailStr | None
    address: str | None
    created_at: datetime