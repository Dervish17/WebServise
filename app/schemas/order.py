from pydantic import BaseModel


class OrderCreate(BaseModel):
    title: str
    description: str
    equipment_id: int

class AssignOrderRequest(BaseModel):
    user_id: int