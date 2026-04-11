from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.normalization import clean_required_text
from app.models.order_item import OrderItem
from app.services.order_service import get_order_by_id


def _parse_decimal(value, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некорректное значение поля: {field_name}",
        )
    return parsed.quantize(Decimal("0.01"))


def _calculate_order_total(db: Session, order_id: int) -> Decimal | None:
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    if not items:
        return None

    total = sum((item.line_total for item in items), Decimal("0.00"))
    return total.quantize(Decimal("0.01"))


def add_order_item(
    db: Session,
    order_id: int,
    title: str,
    quantity,
    unit_price,
) -> OrderItem:
    order = get_order_by_id(db, order_id)

    try:
        title = clean_required_text(title, "Название позиции")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    quantity = _parse_decimal(quantity, "Количество")
    unit_price = _parse_decimal(unit_price, "Цена")

    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Количество должно быть больше нуля",
        )

    if unit_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Цена не может быть отрицательной",
        )

    item = OrderItem(
        order_id=order.id,
        title=title,
        quantity=quantity,
        unit_price=unit_price,
    )

    db.add(item)
    db.flush()

    order.total_cost = _calculate_order_total(db, order.id)

    db.commit()
    db.refresh(item)

    return item


def delete_order_item(
    db: Session,
    order_id: int,
    item_id: int,
) -> None:
    order = get_order_by_id(db, order_id)

    item = (
        db.query(OrderItem)
        .filter(OrderItem.id == item_id, OrderItem.order_id == order.id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция сметы не найдена",
        )

    db.delete(item)
    db.flush()

    order.total_cost = _calculate_order_total(db, order.id)

    db.commit()