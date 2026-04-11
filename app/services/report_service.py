from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models.order import Order
from app.models.status_history import StatusHistory
from app.models.user import User

COMPLETION_STATUSES = {
    OrderStatus.done.value,
    OrderStatus.awaiting_payment.value,
    OrderStatus.closed.value,
}


def parse_report_dates(
    date_from_raw: str | None,
    date_to_raw: str | None,
) -> tuple[date, date]:
    today = date.today()
    first_day = today.replace(day=1)

    date_from = date.fromisoformat(date_from_raw) if date_from_raw else first_day
    date_to = date.fromisoformat(date_to_raw) if date_to_raw else today

    if date_from > date_to:
        raise ValueError("Дата начала периода не может быть позже даты окончания")

    return date_from, date_to


def _dt_range(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(date_from, time.min)
    end_dt = datetime.combine(date_to + timedelta(days=1), time.min)
    return start_dt, end_dt


def _status_label(status_value: str) -> str:
    labels = {
        OrderStatus.new.value: "Новая",
        OrderStatus.diagnostics.value: "Диагностика",
        OrderStatus.estimate_approved.value: "Смета согласована",
        OrderStatus.in_progress.value: "В работе",
        OrderStatus.done.value: "Выполнена",
        OrderStatus.awaiting_payment.value: "Ожидание оплаты",
        OrderStatus.closed.value: "Закрыта",
    }
    return labels.get(status_value, status_value)


def _person_name(user: User | None) -> str:
    if not user:
        return "—"
    full_name = " ".join(
        part for part in [user.last_name, user.first_name, user.middle_name] if part
    ).strip()
    return full_name or user.email or "—"


def build_reports_context(
    db: Session,
    date_from: date,
    date_to: date,
) -> dict:
    start_dt, end_dt = _dt_range(date_from, date_to)

    created_orders = (
        db.query(Order)
        .filter(Order.created_at >= start_dt, Order.created_at < end_dt)
        .all()
    )
    total_orders = len(created_orders)

    status_counts_map: dict[str, int] = defaultdict(int)
    for order in created_orders:
        status_counts_map[order.status] += 1

    status_order = [
        OrderStatus.new.value,
        OrderStatus.diagnostics.value,
        OrderStatus.estimate_approved.value,
        OrderStatus.in_progress.value,
        OrderStatus.done.value,
        OrderStatus.awaiting_payment.value,
        OrderStatus.closed.value,
    ]

    status_counts = [
        {
            "status": status_value,
            "label": _status_label(status_value),
            "count": status_counts_map.get(status_value, 0),
        }
        for status_value in status_order
    ]

    completion_rows = (
        db.query(StatusHistory)
        .filter(
            StatusHistory.new_status.in_(tuple(COMPLETION_STATUSES)),
            StatusHistory.changed_at >= start_dt,
            StatusHistory.changed_at < end_dt,
        )
        .order_by(StatusHistory.order_id.asc(), StatusHistory.changed_at.asc())
        .all()
    )

    first_completion_by_order: dict[int, datetime] = {}
    for row in completion_rows:
        first_completion_by_order.setdefault(row.order_id, row.changed_at)

    completed_orders = []
    if first_completion_by_order:
        completed_orders = (
            db.query(Order)
            .filter(Order.id.in_(list(first_completion_by_order.keys())))
            .all()
        )

    durations_hours: list[float] = []
    for order in completed_orders:
        completed_at = first_completion_by_order.get(order.id)
        if completed_at and order.created_at:
            diff_hours = (completed_at - order.created_at).total_seconds() / 3600
            if diff_hours >= 0:
                durations_hours.append(diff_hours)

    avg_completion_hours = (
        round(sum(durations_hours) / len(durations_hours), 1)
        if durations_hours
        else None
    )
    avg_completion_days = (
        round(avg_completion_hours / 24, 1)
        if avg_completion_hours is not None
        else None
    )

    engineers = (
        db.query(User)
        .filter(User.role == "engineer", User.is_active.is_(True))
        .order_by(User.email.asc())
        .all()
    )

    completed_count_by_engineer: dict[int, int] = defaultdict(int)
    for order in completed_orders:
        if order.assigned_to:
            completed_count_by_engineer[order.assigned_to] += 1

    engineer_rows = []
    for engineer in engineers:
        assigned_orders = (
            db.query(Order)
            .filter(
                Order.assigned_to == engineer.id,
                Order.created_at >= start_dt,
                Order.created_at < end_dt,
            )
            .all()
        )

        active_now = sum(
            1
            for order in assigned_orders
            if order.status not in {OrderStatus.closed.value}
        )

        engineer_rows.append(
            {
                "engineer_id": engineer.id,
                "engineer_name": _person_name(engineer),
                "assigned_count": len(assigned_orders),
                "completed_count": completed_count_by_engineer.get(engineer.id, 0),
                "active_count": active_now,
            }
        )

    engineer_rows.sort(
        key=lambda row: (row["assigned_count"], row["completed_count"]),
        reverse=True,
    )

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_orders": total_orders,
        "completed_orders_count": len(completed_orders),
        "avg_completion_hours": avg_completion_hours,
        "avg_completion_days": avg_completion_days,
        "status_counts": status_counts,
        "engineer_rows": engineer_rows,
    }