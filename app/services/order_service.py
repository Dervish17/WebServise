from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.equipment import Equipment
from app.models.user import User


def create_order(
    db: Session,
    title: str,
    description: str,
    equipment_id: int,
    current_user
):
    # 🔍 находим оборудование
    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id
    ).first()

    if not equipment:
        raise Exception("Equipment not found")

    # 🧠 создаём заказ
    order = Order(
        title=title,
        description=description,
        equipment_id=equipment_id,
        client_id=equipment.client_id,   # 👈 ВАЖНО
        created_by=current_user.id,      # 👈 кто создал
        status="new"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order

def assign_order(db, order_id: int, user_id: int, current_user):
    # 🔍 проверяем заказ
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise Exception("Order not found")

    # 🔍 проверяем пользователя (инженера)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise Exception("User not found")

    # 🔒 проверка роли
    if user.role != "engineer":
        raise Exception("User is not an engineer")

    # 🔒 (опционально) кто может назначать
    if current_user.role not in ["admin"]:
        raise Exception("Not enough permissions")

    # ✅ назначаем
    order.assigned_to = user.id

    db.commit()
    db.refresh(order)

    return order