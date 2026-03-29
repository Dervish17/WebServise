from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.enums import OrderStatus
from app.db.session import get_db
from app.services.order_service import filter_orders, get_order_by_id, add_comment, change_status, assign_order
from app.models.order_log import OrderLog
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/app/orders")
def orders_page(request: Request):
    return templates.TemplateResponse(
        request,
        "orders/page.html",
        {},
    )


@router.get("/app/orders/table")
def orders_table(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    orders = filter_orders(
        db=db,
        status=status,
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
):
    current_user = get_ui_user(db)

    add_comment(
        db=db,
        order_id=order_id,
        text=text,
        current_user=current_user,
    )

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

    engineers = (
        db.query(User)
        .filter(User.role == "engineer")
        .order_by(User.email.asc())
        .all()
    )

    return render_order_detail(request, db, order_id)

def get_ui_user(db: Session) -> User:
    user = db.query(User).order_by(User.id.asc()).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found for UI actions",
        )

    return user

@router.post("/app/orders/{order_id}/status")
def change_status_ui(
    order_id: int,
    request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_ui_user(db)

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
):
    current_user = get_ui_user(db)

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

    engineers = (
        db.query(User)
        .filter(User.role == "engineer")
        .order_by(User.email.asc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "orders/_detail.html",
        {
            "order": order,
            "comments": comments,
            "engineers": engineers,
        },
    )