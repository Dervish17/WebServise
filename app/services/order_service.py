from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.enums import OrderStatus
from app.core.normalization import clean_optional_text, clean_required_text
from app.models.equipment import Equipment
from app.models.order import Order
from app.models.order_log import OrderLog
from app.models.user import User
from app.models.client import Client
from app.models.status_history import StatusHistory

ALLOWED_TRANSITIONS = {
    OrderStatus.new.value: [OrderStatus.diagnostics.value],
    OrderStatus.diagnostics.value: [OrderStatus.estimate_approved.value],
    OrderStatus.estimate_approved.value: [OrderStatus.in_progress.value],
    OrderStatus.in_progress.value: [OrderStatus.done.value],
    OrderStatus.done.value: [OrderStatus.awaiting_payment.value],
    OrderStatus.awaiting_payment.value: [OrderStatus.closed.value],
    OrderStatus.closed.value: [],
}

def _validate_total_cost(total_cost):
    if total_cost is not None and total_cost < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Стоимость не может быть отрицательной",
        )

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

def _can_change_status(
    current_user: User,
    order: Order,
    old_status: str,
    new_status: str,
) -> bool:
    if current_user.role in {"admin", "manager"}:
        return True

    if current_user.role == "engineer":
        return (
            order.assigned_to == current_user.id
            and (
                (old_status == OrderStatus.estimate_approved.value and new_status == OrderStatus.in_progress.value)
                or
                (old_status == OrderStatus.in_progress.value and new_status == OrderStatus.done.value)
            )
        )

    return False


def create_order(
        db: Session,
        title: str,
        description: str,
        equipment_id: int,
        current_user: User,
        total_cost=None,
) -> Order:
    _validate_total_cost(total_cost)

    try:
        title = clean_required_text(title, "Название заявки")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    description = clean_optional_text(description)
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

    description = "Создана заявка"

    if order.total_cost is not None:
        description += f", стоимость: {order.total_cost}"

    _create_order_log(
        db=db,
        order_id=order.id,
        action="create",
        description=description,
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
        search: str | None = None,
        sort: str = "newest",
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
    query = query.join(Order.client).join(Order.equipment)

    if status:
        query = query.filter(Order.status == status)

    if client_id:
        query = query.filter(Order.client_id == client_id)

    if assigned_to:
        query = query.filter(Order.assigned_to == assigned_to)

    if created_by:
        query = query.filter(Order.created_by == created_by)

    if search:
        query = query.filter(
            (Order.title.ilike(f"%{search}%")) |
            (Order.description.ilike(f"%{search}%")) |
            (Client.name.ilike(f"%{search}%")) |
            (Equipment.name.ilike(f"%{search}%")) |
            (Equipment.model.ilike(f"%{search}%")) |
            (Equipment.serial_number.ilike(f"%{search}%"))
        )

    if sort == "oldest":
        query = query.order_by(Order.created_at.asc())
    else:
        query = query.order_by(Order.created_at.desc())

    return query.offset(offset).limit(limit).all()


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

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected engineer is inactive",
        )

    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to assign engineer",
        )

    order.assigned_to = user.id

    engineer_name = " ".join(
        part for part in [user.last_name, user.first_name, user.middle_name] if part
    ).strip()

    _create_order_log(
        db=db,
        order_id=order.id,
        action="assign",
        description=f"Назначен инженер: {engineer_name if engineer_name else user.email}",
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
            detail=f"Нельзя изменить статус с {order.status} на {new_status.value}",
        )

    if not _can_change_status(current_user, order, order.status, new_status.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для смены этого статуса",
        )

    old_status = order.status
    order.status = new_status.value

    status_names = {
        "new": "Новая",
        "diagnostics": "Диагностика",
        "estimate_approved": "Смета согласована",
        "in_progress": "В работе",
        "done": "Выполнена",
        "awaiting_payment": "Ожидание оплаты",
        "closed": "Закрыта",
    }

    history = StatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=new_status.value,
        changed_by=current_user.id,
    )
    db.add(history)

    _create_order_log(
        db=db,
        order_id=order.id,
        action="status_change",
        description=(
            f"Статус изменён: "
            f"{status_names.get(old_status, old_status)} → "
            f"{status_names.get(new_status.value, new_status.value)}"
        ),
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
    try:
        text = clean_required_text(text, "Комментарий")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

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


def update_order(
        db: Session,
        order_id: int,
        title: str,
        description: str | None = None,
        total_cost=None,
) -> Order:
    _validate_total_cost(total_cost)

    try:
        title = clean_required_text(title, "Название заявки")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    description = clean_optional_text(description)

    order = get_order_by_id(db, order_id)

    order.title = title
    order.description = description
    order.total_cost = total_cost

    db.commit()
    db.refresh(order)

    return order


def delete_order(db: Session, order_id: int) -> None:
    order = get_order_by_id(db, order_id)

    db.query(OrderLog).filter(OrderLog.order_id == order.id).delete()
    db.query(StatusHistory).filter(StatusHistory.order_id == order.id).delete()

    db.delete(order)
    db.commit()
