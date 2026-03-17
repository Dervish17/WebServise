from pydantic import BaseModel

class EquipmentCreate(BaseModel):
    name: str
    client_id: int

class EquipmentResponse(BaseModel):
    id: int
    name: str
    client_id: int

    class Config:
        from_attributes = True