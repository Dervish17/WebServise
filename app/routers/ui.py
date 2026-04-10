from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import jwt, JWTError
from sqlalchemy.orm import Session, joinedload

from app.core.config import SECRET_KEY, ALGORITHM
from app.core.enums import OrderStatus
from app.db.session import get_db
from app.services.order_service import filter_orders, get_order_by_id, add_comment, change_status, assign_order, \
    update_order, delete_order, create_order
from app.models.order_log import OrderLog
from app.models.user import User
from app.models.order import Order
from app.models.equipment import Equipment
from app.services.equipment_service import create_equipment, get_equipment_by_id, update_equipment, delete_equipment, \
    get_all_equipment
from app.services.auth_service import login_user
from app.services.user_service import create_user, update_user, delete_user, toggle_user_active
from app.services.client_service import get_all_clients, get_client_by_id, create_client, update_client, delete_client
from app.core.dependencies import get_current_user

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

def render_alert(request: Request, text: str, kind: str = "success", status_code: int = 200):
    return templates.TemplateResponse(
        request,
        "shared/_alert.html",
        {
            "text": text,
            "kind": kind,
        },
        status_code=status_code,
    )

def get_current_ui_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_from_token_value(access_token, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user


def get_user_from_token_value(token: str | None, db: Session) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_raw = payload.get("sub")
    except JWTError:
        return None

    if not user_id_raw:
        return None

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user

@router.get("/app")
def app_root():
    return RedirectResponse(url="/app/login", status_code=303)

@router.get("/app/orders")
def orders_page(
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
    search: str | None = None,
    sort: str = "newest",
    db: Session = Depends(get_db),
):
    clients = get_all_clients(db, search=search, sort=sort)

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
    search: str | None = None,
    sort: str = "newest",
    db: Session = Depends(get_db),
):
    equipments = get_all_equipment(db, search=search, sort=sort)

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
        db.query(User)
        .filter(User.role == "engineer")
        .order_by(User.email.asc())
        .all()
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


@router.get("/app/clients/{client_id}/page")
def client_page(
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
        "clients/client_page.html",
        {
            "client": client,
            "equipments": equipments,
            "orders": orders,
        },
    )


@router.get("/app/equipment/{equipment_id}/page")
def equipment_page_single(
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
        "equipment/equipment_page.html",
        {
            "equipment": equipment,
            "orders": orders,
        },
    )


@router.get("/app/clients/{client_id}/edit")
def edit_client_form(
        client_id: int,
        request: Request,
        db: Session = Depends(get_db),
):
    client = get_client_by_id(db, client_id)

    return templates.TemplateResponse(
        request,
        "clients/_edit.html",
        {"client": client},
    )


@router.post("/app/clients/{client_id}/edit")
def edit_client_submit(
        client_id: int,
        request: Request,
        name: str = Form(...),
        contact_person: str = Form(None),
        phone: str = Form(None),
        email: str = Form(None),
        address: str = Form(None),
        notes: str = Form(None),
        db: Session = Depends(get_db),
):
    update_client(
        db=db,
        client_id=client_id,
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
    )

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


@router.get("/app/equipment/{equipment_id}/edit")
def edit_equipment_form(
        equipment_id: int,
        request: Request,
        db: Session = Depends(get_db),
):
    equipment = get_equipment_by_id(db, equipment_id)

    return templates.TemplateResponse(
        request,
        "equipment/_edit.html",
        {"equipment": equipment},
    )


@router.post("/app/equipment/{equipment_id}/edit")
def edit_equipment_submit(
        equipment_id: int,
        request: Request,
        name: str = Form(...),
        model: str = Form(None),
        serial_number: str = Form(None),
        manufacturer: str = Form(None),
        db: Session = Depends(get_db),
):
    update_equipment(
        db=db,
        equipment_id=equipment_id,
        name=name,
        model=model,
        serial_number=serial_number,
        manufacturer=manufacturer,
    )

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


@router.delete("/app/clients/{client_id}")
def delete_client_ui(
    client_id: int,
    request: Request,
    redirect_to_list: bool = False,
    db: Session = Depends(get_db),
):
    try:
        delete_client(db, client_id)

        if redirect_to_list:
            response = HTMLResponse("")
            response.headers["HX-Redirect"] = "/app/clients"
            return response

        response = render_alert(request, "Клиент удалён.", "success")
        response.headers["HX-Trigger"] = "refreshClients"
        return response

    except HTTPException as e:
        return render_alert(request, e.detail, "error")


@router.delete("/app/equipment/{equipment_id}")
def delete_equipment_ui(
    equipment_id: int,
    request: Request,
    redirect_to_list: bool = False,
    db: Session = Depends(get_db),
):
    try:
        delete_equipment(db, equipment_id)

        if redirect_to_list:
            response = HTMLResponse("")
            response.headers["HX-Redirect"] = "/app/equipment"
            return response

        response = render_alert(request, "Оборудование удалено.", "success")
        response.headers["HX-Trigger"] = "refreshEquipment"
        return response

    except HTTPException as e:
        return render_alert(request, e.detail, "error")

@router.get("/app/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {},
    )

@router.post("/app/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        result = login_user(db, email, password)
    except HTTPException:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Неверный email, пароль или пользователь деактивирован.",
                "email": email,
            },
            status_code=400,
        )

    token = None

    if isinstance(result, str):
        token = result
    elif isinstance(result, dict):
        token = result.get("access_token")

    if not token:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Неверный email, пароль или пользователь деактивирован.",
                "email": email,
            },
            status_code=400,
        )

    response = RedirectResponse(url="/app/orders", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )

    return response


@router.get("/app/logout")
def logout():
    response = RedirectResponse(url="/app/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response

@router.get("/app/users")
def users_page(request: Request):
    return templates.TemplateResponse(
        request,
        "users/page.html",
        {},
    )


@router.get("/app/users/table")
def users_table(
    request: Request,
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.desc()).all()

    return templates.TemplateResponse(
        request,
        "users/_table.html",
        {"users": users},
    )

@router.post("/app/users/create")
def create_user_ui(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    last_name: str = Form(None),
    first_name: str = Form(None),
    middle_name: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(request, "Только администратор может создавать пользователей.", "error")

    create_user(
        db=db,
        email=email,
        password=password,
        role=role,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
    )

    response = templates.TemplateResponse(
        request,
        "users/_create_result.html",
        {},
    )
    response.headers["HX-Trigger"] = "refreshUsers"
    return response

@router.get("/app/users/{user_id}/edit")
def edit_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(request, "Только администратор может редактировать пользователей.", "error")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return render_alert(request, "Пользователь не найден.", "error")

    return templates.TemplateResponse(
        request,
        "users/_edit.html",
        {"user": user},
    )

@router.post("/app/users/{user_id}/edit")
def edit_user_submit(
    user_id: int,
    request: Request,
    email: str = Form(...),
    role: str = Form(...),
    last_name: str = Form(None),
    first_name: str = Form(None),
    middle_name: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(request, "Только администратор может редактировать пользователей.", "error")

    try:
        update_user(
            db=db,
            user_id=user_id,
            email=email,
            role=role,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
        )
    except ValueError:
        return render_alert(request, "Пользователь не найден.", "error")

    response = HTMLResponse("")
    response.headers["HX-Trigger"] = "refreshUsers"
    return response

@router.delete("/app/users/{user_id}")
def delete_user_ui(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(request, "Только администратор может удалять пользователей.", "error")

    try:
        delete_user(
            db=db,
            user_id=user_id,
            current_user_id=current_user.id,
        )

        response = HTMLResponse("")
        response.headers["HX-Trigger"] = "refreshUsers"
        return response

    except HTTPException as e:
        return render_alert(request, e.detail, "error")

@router.post("/app/users/{user_id}/toggle-active")
def toggle_user_active_ui(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(request, "Только администратор может менять статус пользователей.", "error")

    try:
        toggle_user_active(
            db=db,
            user_id=user_id,
            current_user_id=current_user.id,
        )

        response = HTMLResponse("")
        response.headers["HX-Trigger"] = "refreshUsers"
        return response

    except HTTPException as e:
        return render_alert(request, e.detail, "error")