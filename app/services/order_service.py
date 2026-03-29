from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.enums import OrderStatus
from app.models.equipment import Equipment
from app.models.order import Order
from app.models.order_log import OrderLog
from app.models.user import User


ALLOWED_TRANSITIONS = {
    OrderStatus.new.value: [OrderStatus.in_progress.value],
    OrderStatus.in_progress.value: [OrderStatus.done.value],
    OrderStatus.done.value: [],
}


def _create_order_log(
    db: Session,
    order_id: int,
    action: str,
    description: str,
    user_id: int,
) -> OrderLog:
    log = OrderLog(
        order_id=order_id,
        action=action,
        description=description,
        user_id=user_id,
    )
    db.add(log)
    return log


def create_order(
    db: Session,
    title: str,
    description: str,
    equipment_id: int,
    current_user: User,
    total_cost=None,
) -> Order:
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    order = Order(
        title=title,
        description=description,
        equipment_id=equipment_id,
        client_id=equipment.client_id,
        created_by=current_user.id,
        status=OrderStatus.new.value,
        total_cost=total_cost,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    _create_order_log(
        db=db,
        order_id=order.id,
        action="create",
        description="Создана заявка",
        user_id=current_user.id,
    )
    db.commit()

    return order


def filter_orders(
    db: Session,
    status: str | None = None,
    client_id: int | None = None,
    assigned_to: int | None = None,
    created_by: int | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[Order]:
    query = (
        db.query(Order)
        .options(
            joinedload(Order.client),
            joinedload(Order.equipment),
            joinedload(Order.creator),
            joinedload(Order.assignee),
        )
    )

    if status:
        query = query.filter(Order.status == status)

    if client_id:
        query = query.filter(Order.client_id == client_id)

    if assigned_to:
        query = query.filter(Order.assigned_to == assigned_to)

    if created_by:
        query = query.filter(Order.created_by == created_by)

    return (
        query.order_by(Order.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_order_by_id(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(
            joinedload(Order.client),
            joinedload(Order.equipment),
            joinedload(Order.creator),
            joinedload(Order.assignee),
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


def assign_order(
    db: Session,
    order_id: int,
    user_id: int,
    current_user: User,
) -> Order:
    order = get_order_by_id(db, order_id)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role != "engineer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not an engineer",
        )

    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to assign engineer",
        )

    order.assigned_to = user.id

    _create_order_log(
        db=db,
        order_id=order.id,
        action="assign",
        description=f"Назначен инженер id={user.id}",
        user_id=current_user.id,
    )

    db.commit()
    db.refresh(order)

    return order


def change_status(
    db: Session,
    order_id: int,
    new_status: OrderStatus,
    current_user: User,
) -> Order:
    order = get_order_by_id(db, order_id)

    allowed = ALLOWED_TRANSITIONS.get(order.status, [])
    if new_status.value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change status from {order.status} to {new_status.value}",
        )

    if current_user.role != "admin" and order.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned engineer or admin can change status",
        )

    old_status = order.status
    order.status = new_status.value

    _create_order_log(
        db=db,
        order_id=order.id,
        action="status_change",
        description=f"{old_status} -> {new_status.value}",
        user_id=current_user.id,
    )

    db.commit()
    db.refresh(order)

    return order


def add_comment(
    db: Session,
    order_id: int,
    text: str,
    current_user: User,
) -> OrderLog:
    order = get_order_by_id(db, order_id)

    log = OrderLog(
        order_id=order.id,
        action="comment",
        description=text,
        user_id=current_user.id,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log