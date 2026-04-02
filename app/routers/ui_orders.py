from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.db.session import get_db
from app.models.equipment import Equipment
from app.models.order_log import OrderLog
from app.models.user import User
from app.services.order_service import (
    add_comment,
    assign_order,
    change_status,
    create_order,
    delete_order,
    filter_orders,
    get_order_by_id,
    update_order,
)
from app.routers.ui_shared import get_current_ui_user, render_alert, templates

router = APIRouter(tags=["ui"])


@router.get("/app")
def app_root():
    return RedirectResponse(url="/app/login", status_code=303)


@router.get("/app/orders")
def orders_page(
    request: Request,
    db: Session = Depends(get_db),
):
    equipments = db.query(Equipment).order_by(Equipment.id.desc()).all()

    return templates.TemplateResponse(
        request,
        "orders/page.html",
        {"equipments": equipments},
    )


@router.get("/app/orders/table")
def orders_table(
    request: Request,
    status: str | None = None,
    search: str | None = None,
    sort: str = "newest",
    db: Session = Depends(get_db),
):
    orders = filter_orders(
        db=db,
        status=status,
        search=search,
        sort=sort,
        limit=20,
        offset=0,
    )

    return templates.TemplateResponse(
        request,
        "orders/_table.html",
        {"orders": orders},
    )


@router.get("/app/orders/{order_id}/detail")
def order_detail(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    return render_order_detail(request, db, order_id)


@router.post("/app/orders/{order_id}/comment")
def add_comment_ui(
    order_id: int,
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    add_comment(
        db=db,
        order_id=order_id,
        text=text,
        current_user=current_user,
    )

    return render_order_detail(request, db, order_id)


@router.post("/app/orders/{order_id}/status")
def change_status_ui(
    order_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    change_status(
        db=db,
        order_id=order_id,
        new_status=OrderStatus(new_status),
        current_user=current_user,
    )

    response = render_order_detail(request, db, order_id)
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


@router.post("/app/orders/{order_id}/assign")
def assign_order_ui(
    order_id: int,
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    assign_order(
        db=db,
        order_id=order_id,
        user_id=user_id,
        current_user=current_user,
    )

    response = render_order_detail(request, db, order_id)
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


def render_order_detail(request: Request, db: Session, order_id: int):
    order = get_order_by_id(db, order_id)

    comments = (
        db.query(OrderLog)
        .filter(
            OrderLog.order_id == order_id,
            OrderLog.action == "comment",
        )
        .order_by(OrderLog.created_at.desc())
        .all()
    )

    logs = (
        db.query(OrderLog)
        .filter(
            OrderLog.order_id == order_id,
            OrderLog.action != "comment",
        )
        .order_by(OrderLog.created_at.desc())
        .all()
    )

    engineers = (
        db.query(User)
        .filter(
            User.role == "engineer",
            User.is_active == True,
        )
        .order_by(User.email.asc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "orders/_detail.html",
        {
            "order": order,
            "comments": comments,
            "logs": logs,
            "engineers": engineers,
        },
    )


@router.get("/app/orders/{order_id}/page")
def order_page(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    order = get_order_by_id(db, order_id)

    comments = (
        db.query(OrderLog)
        .filter(
            OrderLog.order_id == order_id,
            OrderLog.action == "comment",
        )
        .order_by(OrderLog.created_at.desc())
        .all()
    )

    logs = (
        db.query(OrderLog)
        .filter(
            OrderLog.order_id == order_id,
            OrderLog.action != "comment",
        )
        .order_by(OrderLog.created_at.desc())
        .all()
    )

    engineers = (
        db.query(User).filter(User.role == "engineer").order_by(User.email.asc()).all()
    )

    return templates.TemplateResponse(
        request,
        "orders/order_page.html",
        {
            "order": order,
            "comments": comments,
            "logs": logs,
            "engineers": engineers,
        },
    )


@router.get("/app/orders/{order_id}/edit")
def edit_order_form(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    order = get_order_by_id(db, order_id)

    return templates.TemplateResponse(
        request,
        "orders/_edit.html",
        {"order": order},
    )


@router.post("/app/orders/{order_id}/edit")
def edit_order_submit(
    order_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    total_cost: float | None = Form(None),
    db: Session = Depends(get_db),
):
    update_order(
        db=db,
        order_id=order_id,
        title=title,
        description=description,
        total_cost=total_cost,
    )

    return render_order_detail(request, db, order_id)


@router.delete("/app/orders/{order_id}")
def delete_order_ui(
    order_id: int,
    request: Request,
    redirect_to_list: bool = False,
    db: Session = Depends(get_db),
):
    delete_order(db, order_id)

    if redirect_to_list:
        response = HTMLResponse("")
        response.headers["HX-Redirect"] = "/app/orders"
        return response

    response = render_alert(request, "Заявка удалена.", "success")
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


@router.post("/app/orders/create")
def create_order_ui(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    equipment_id: int = Form(...),
    total_cost: float | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    order = create_order(
        db=db,
        title=title,
        description=description,
        equipment_id=equipment_id,
        current_user=current_user,
        total_cost=total_cost,
    )

    response = templates.TemplateResponse(
        request,
        "orders/_create_result.html",
        {"order": order},
    )
    response.headers["HX-Trigger"] = "refreshOrders"
    return response
