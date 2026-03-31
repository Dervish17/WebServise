from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.core.enums import OrderStatus
from app.db.session import get_db
from app.services.order_service import filter_orders, get_order_by_id, add_comment, change_status, assign_order
from app.models.order_log import OrderLog
from app.models.user import User
from app.models.order import Order
from app.models.equipment import Equipment
from app.services.equipment_service import create_equipment, get_equipment_by_id, get_all_equipment
from app.services.client_service import get_all_clients, get_client_by_id, create_client
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
            "logs": logs,
            "engineers": engineers,
        },
    )

@router.get("/app/clients")
def clients_page(request: Request):
    return templates.TemplateResponse(
        request,
        "clients/page.html",
        {},
    )


@router.get("/app/clients/table")
def clients_table(
    request: Request,
    db: Session = Depends(get_db),
):
    clients = get_all_clients(db)

    return templates.TemplateResponse(
        request,
        "clients/_table.html",
        {"clients": clients},
    )

@router.get("/app/clients/{client_id}/detail")
def client_detail(
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    client = get_client_by_id(db, client_id)

    equipments = (
        db.query(Equipment)
        .filter(Equipment.client_id == client_id)
        .order_by(Equipment.id.desc())
        .all()
    )

    orders = (
        db.query(Order)
        .options(joinedload(Order.equipment))
        .filter(Order.client_id == client_id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "clients/_detail.html",
        {
            "client": client,
            "equipments": equipments,
            "orders": orders,
        },
    )

@router.post("/app/clients/create")
def create_client_ui(
    request: Request,
    name: str = Form(...),
    contact_person: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    address: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db),
):
    create_client(
        db=db,
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
    )

    clients = get_all_clients(db)

    response = templates.TemplateResponse(
        request,
        "clients/_table.html",
        {"clients": clients},
    )
    response.headers["HX-Trigger"] = "refreshClients"
    return response

@router.post("/app/clients/{client_id}/equipment/create")
def create_equipment_ui(
    client_id: int,
    request: Request,
    name: str = Form(...),
    model: str = Form(None),
    serial_number: str = Form(None),
    manufacturer: str = Form(None),
    db: Session = Depends(get_db),
):
    create_equipment(
        db=db,
        name=name,
        client_id=client_id,
        model=model,
        serial_number=serial_number,
        manufacturer=manufacturer,
    )

    client = get_client_by_id(db, client_id)

    equipments = (
        db.query(Equipment)
        .filter(Equipment.client_id == client_id)
        .order_by(Equipment.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "clients/_detail.html",
        {
            "client": client,
            "equipments": equipments,
        },
    )

@router.get("/app/equipment")
def equipment_page(request: Request):
    return templates.TemplateResponse(
        request,
        "equipment/page.html",
        {},
    )


@router.get("/app/equipment/table")
def equipment_table(
    request: Request,
    db: Session = Depends(get_db),
):
    equipments = (
        db.query(Equipment)
        .options(joinedload(Equipment.client))
        .order_by(Equipment.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "equipment/_table.html",
        {"equipments": equipments},
    )

@router.get("/app/equipment/{equipment_id}/detail")
def equipment_detail(
    equipment_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    equipment = get_equipment_by_id(db, equipment_id)

    orders = (
        db.query(Order)
        .filter(Order.equipment_id == equipment_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "equipment/_detail.html",
        {
            "equipment": equipment,
            "orders": orders,
        },
    )