from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.order import AssignOrderRequest

from app.db.session import get_db
from app.schemas.order import OrderCreate
from app.services.order_service import create_order, assign_order
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/")
def create_order_endpoint(
    title: str,
    description: str,
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return create_order(
        db,
        title,
        description,
        equipment_id,
        current_user
    )

@router.put("/{order_id}/assign")
def assign_order_endpoint(
    order_id: int,
    data: AssignOrderRequest,  # 👈 теперь body
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return assign_order(
        db,
        order_id,
        data.user_id,  # 👈 берём из body
        current_user
    )