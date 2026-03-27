from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.order import Order
from app.models.order_log import OrderLog
from app.models.user import User
from app.schemas.order import (
    AssignOrderRequest,
    ChangeStatusRequest,
    CreateCommentRequest,
    OrderCreate,
    OrderResponse,
)
from app.schemas.order_log import OrderLogResponse
from app.services.order_service import (
    add_comment,
    assign_order,
    change_status,
    create_order,
    filter_orders,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_order(
        db=db,
        title=order.title,
        description=order.description,
        equipment_id=order.equipment_id,
        current_user=current_user,
    )


@router.get("/", response_model=list[OrderResponse])
def get_orders(
    status: str | None = None,
    client_id: int | None = None,
    assigned_to: int | None = None,
    created_by: int | None = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return filter_orders(
        db=db,
        status=status,
        client_id=client_id,
        assigned_to=assigned_to,
        created_by=created_by,
        limit=limit,
        offset=offset,
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.put("/{order_id}/assign", response_model=OrderResponse)
def assign_order_endpoint(
    order_id: int,
    data: AssignOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return assign_order(
        db=db,
        order_id=order_id,
        user_id=data.user_id,
        current_user=current_user,
    )


@router.put("/{order_id}/status", response_model=OrderResponse)
def change_status_endpoint(
    order_id: int,
    data: ChangeStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_status(
        db=db,
        order_id=order_id,
        new_status=data.status,
        current_user=current_user,
    )


@router.post("/{order_id}/comment", response_model=OrderLogResponse, status_code=status.HTTP_201_CREATED)
def add_comment_endpoint(
    order_id: int,
    data: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return add_comment(
        db=db,
        order_id=order_id,
        text=data.text,
        current_user=current_user,
    )


@router.get("/{order_id}/logs", response_model=list[OrderLogResponse])
def get_order_logs(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return (
        db.query(OrderLog)
        .filter(OrderLog.order_id == order_id)
        .order_by(OrderLog.created_at.desc())
        .all()
    )