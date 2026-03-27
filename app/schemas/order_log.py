from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    action: str
    description: str
    user_id: int
    created_at: datetime