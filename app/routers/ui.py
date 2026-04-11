from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from app.core.config import ALGORITHM, SECRET_KEY
from app.core.enums import OrderStatus
from app.db.session import get_db
from app.models.equipment import Equipment
from app.models.order import Order
from app.models.order_log import OrderLog
from app.models.user import User
from app.services.auth_service import login_user
from app.services.client_service import (
    create_client,
    delete_client,
    get_all_clients,
    get_client_by_id,
    update_client,
)
from app.services.equipment_service import (
    create_equipment,
    delete_equipment,
    get_all_equipment,
    get_equipment_by_id,
    update_equipment,
)
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
from app.services.user_service import (
    change_user_password,
    create_user,
    delete_user,
    toggle_user_active,
    update_profile,
    update_user,
)

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

DbSession = Annotated[Session, Depends(get_db)]


def render_alert(
    request: Request,
    text: str,
    kind: str = "success",
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "shared/_alert.html",
        {
            "text": text,
            "kind": kind,
        },
        status_code=status_code,
    )


def render_http_error_alert(request: Request, exc: HTTPException) -> HTMLResponse:
    return render_alert(
        request,
        str(exc.detail),
        kind="error",
        status_code=exc.status_code,
    )

def render_hx_alert(
    request: Request,
    text: str,
    kind: str = "error",
    target: str | None = None,
) -> HTMLResponse:
    response = render_alert(
        request,
        text=text,
        kind=kind,
        status_code=status.HTTP_200_OK,
    )

    if target:
        response.headers["HX-Retarget"] = target
        response.headers["HX-Reswap"] = "innerHTML"

    return response


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

    return (
        db.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )


def get_current_ui_user(
    request: Request,
    db: DbSession,
    access_token: str | None = Cookie(default=None),
) -> User:
    user = get_user_from_token_value(access_token, db)

    if not user:
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется авторизация.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user


def require_admin(current_user: Annotated[User, Depends(get_current_ui_user)]) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может выполнять это действие.",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_ui_user)]
AdminUser = Annotated[User, Depends(require_admin)]


def get_client_context(db: Session, client_id: int) -> dict:
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

    return {
        "client": client,
        "equipments": equipments,
        "orders": orders,
    }


def get_equipment_context(db: Session, equipment_id: int) -> dict:
    equipment = get_equipment_by_id(db, equipment_id)

    orders = (
        db.query(Order)
        .filter(Order.equipment_id == equipment_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return {
        "equipment": equipment,
        "orders": orders,
    }


def get_order_context(db: Session, order_id: int) -> dict:
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
            User.is_active.is_(True),
        )
        .order_by(User.email.asc())
        .all()
    )

    return {
        "order": order,
        "comments": comments,
        "logs": logs,
        "engineers": engineers,
    }


def render_client_detail(request: Request, db: Session, client_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "clients/_detail.html",
        get_client_context(db, client_id),
    )


def render_client_page(request: Request, db: Session, client_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "clients/client_page.html",
        get_client_context(db, client_id),
    )


def render_equipment_detail(
    request: Request,
    db: Session,
    equipment_id: int,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "equipment/_detail.html",
        get_equipment_context(db, equipment_id),
    )


def render_equipment_page(
    request: Request,
    db: Session,
    equipment_id: int,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "equipment/equipment_page.html",
        get_equipment_context(db, equipment_id),
    )


def render_order_detail(request: Request, db: Session, order_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "orders/_detail.html",
        get_order_context(db, order_id),
    )


def render_order_page(request: Request, db: Session, order_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "orders/order_page.html",
        get_order_context(db, order_id),
    )


def render_profile_summary(request: Request, user: User) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "users/_profile_summary.html",
        {"user": user},
    )


def render_users_table_partial(request: Request, db: Session) -> HTMLResponse:
    users = db.query(User).order_by(User.id.desc()).all()
    return templates.TemplateResponse(
        request,
        "users/_table.html",
        {"users": users},
    )


# =========================
# Public routes
# =========================

@router.get("/app")
def app_root() -> RedirectResponse:
    return RedirectResponse(url="/app/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/app/login")
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {},
    )


@router.post("/app/login")
def login_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    password: str = Form(...),
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
            status_code=status.HTTP_400_BAD_REQUEST,
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
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    response = RedirectResponse(url="/app/orders", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


@router.get("/app/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/app/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token", path="/")
    return response


# =========================
# Clients
# =========================

@router.get("/app/clients")
def clients_page(
    request: Request,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "clients/page.html",
        {},
    )


@router.get("/app/clients/table")
def clients_table(
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    search: str | None = None,
    sort: str = "newest",
) -> HTMLResponse:
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
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return render_client_detail(request, db, client_id)


@router.get("/app/clients/{client_id}/page")
def client_page(
    client_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return render_client_page(request, db, client_id)


@router.get("/app/clients/{client_id}/edit")
def edit_client_form(
    client_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    client = get_client_by_id(db, client_id)

    return templates.TemplateResponse(
        request,
        "clients/_edit.html",
        {"client": client},
    )


@router.post("/app/clients/create")
def create_client_ui(
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    name: str = Form(...),
    contact_person: str | None = Form(default=None),
    phone: str | None = Form(default=None),
    email: str | None = Form(default=None),
    address: str | None = Form(default=None),
    notes: str | None = Form(default=None),
):
    try:
        create_client(
            db=db,
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            notes=notes,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    clients = get_all_clients(db)

    response = templates.TemplateResponse(
        request,
        "clients/_table.html",
        {"clients": clients},
    )
    response.headers["HX-Trigger"] = "refreshClients"
    return response


@router.post("/app/clients/{client_id}/edit")
def edit_client_submit(
    client_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    name: str = Form(...),
    contact_person: str | None = Form(default=None),
    phone: str | None = Form(default=None),
    email: str | None = Form(default=None),
    address: str | None = Form(default=None),
    notes: str | None = Form(default=None),
):
    try:
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
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    return render_client_detail(request, db, client_id)


@router.delete("/app/clients/{client_id}")
def delete_client_ui(
    client_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    redirect_to_list: bool = False,
):
    try:
        delete_client(db, client_id)
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    if redirect_to_list:
        response = HTMLResponse("")
        response.headers["HX-Redirect"] = "/app/clients"
        return response

    response = render_alert(request, "Клиент удалён.", "success")
    response.headers["HX-Trigger"] = "refreshClients"
    return response


@router.post("/app/clients/{client_id}/equipment/create")
def create_equipment_ui(
    client_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    name: str = Form(...),
    model: str | None = Form(default=None),
    serial_number: str | None = Form(default=None),
    manufacturer: str | None = Form(default=None),
):
    try:
        create_equipment(
            db=db,
            name=name,
            client_id=client_id,
            model=model,
            serial_number=serial_number,
            manufacturer=manufacturer,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    return render_client_detail(request, db, client_id)


# =========================
# Equipment
# =========================

@router.get("/app/equipment")
def equipment_page(
    request: Request,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "equipment/page.html",
        {},
    )


@router.get("/app/equipment/table")
def equipment_table(
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    search: str | None = None,
    sort: str = "newest",
) -> HTMLResponse:
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
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return render_equipment_detail(request, db, equipment_id)


@router.get("/app/equipment/{equipment_id}/page")
def equipment_page_single(
    equipment_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return render_equipment_page(request, db, equipment_id)


@router.get("/app/equipment/{equipment_id}/edit")
def edit_equipment_form(
    equipment_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
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
    db: DbSession,
    _current_user: CurrentUser,
    name: str = Form(...),
    model: str | None = Form(default=None),
    serial_number: str | None = Form(default=None),
    manufacturer: str | None = Form(default=None),
):
    try:
        update_equipment(
            db=db,
            equipment_id=equipment_id,
            name=name,
            model=model,
            serial_number=serial_number,
            manufacturer=manufacturer,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    return render_equipment_detail(request, db, equipment_id)


@router.delete("/app/equipment/{equipment_id}")
def delete_equipment_ui(
    equipment_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    redirect_to_list: bool = False,
):
    try:
        delete_equipment(db, equipment_id)
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    if redirect_to_list:
        response = HTMLResponse("")
        response.headers["HX-Redirect"] = "/app/equipment"
        return response

    response = render_alert(request, "Оборудование удалено.", "success")
    response.headers["HX-Trigger"] = "refreshEquipment"
    return response


# =========================
# Orders
# =========================

@router.get("/app/orders")
def orders_page(
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
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
    db: DbSession,
    _current_user: CurrentUser,
    status: str | None = None,
    search: str | None = None,
    sort: str = "newest",
) -> HTMLResponse:
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
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return render_order_detail(request, db, order_id)


@router.get("/app/orders/{order_id}/page")
def order_page(
    order_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    return render_order_page(request, db, order_id)


@router.get("/app/orders/{order_id}/edit")
def edit_order_form(
    order_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
) -> HTMLResponse:
    order = get_order_by_id(db, order_id)

    return templates.TemplateResponse(
        request,
        "orders/_edit.html",
        {"order": order},
    )


@router.post("/app/orders/create")
def create_order_ui(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    description: str | None = Form(default=None),
    equipment_id: int = Form(...),
    total_cost: float | None = Form(default=None),
):
    try:
        order = create_order(
            db=db,
            title=title,
            description=description,
            equipment_id=equipment_id,
            current_user=current_user,
            total_cost=total_cost,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    response = templates.TemplateResponse(
        request,
        "orders/_create_result.html",
        {"order": order},
    )
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


@router.post("/app/orders/{order_id}/comment")
def add_comment_ui(
    order_id: int,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    text: str = Form(...),
):
    try:
        add_comment(
            db=db,
            order_id=order_id,
            text=text,
            current_user=current_user,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    return render_order_detail(request, db, order_id)


@router.post("/app/orders/{order_id}/status")
def change_status_ui(
    order_id: int,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    new_status: OrderStatus = Form(...),
):
    try:
        change_status(
            db=db,
            order_id=order_id,
            new_status=new_status,
            current_user=current_user,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    response = render_order_detail(request, db, order_id)
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


@router.post("/app/orders/{order_id}/assign")
def assign_order_ui(
    order_id: int,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    user_id: int = Form(...),
):
    try:
        assign_order(
            db=db,
            order_id=order_id,
            user_id=user_id,
            current_user=current_user,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    response = render_order_detail(request, db, order_id)
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


@router.post("/app/orders/{order_id}/edit")
def edit_order_submit(
    order_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    title: str = Form(...),
    description: str | None = Form(default=None),
    total_cost: float | None = Form(default=None),
):
    try:
        update_order(
            db=db,
            order_id=order_id,
            title=title,
            description=description,
            total_cost=total_cost,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    return render_order_detail(request, db, order_id)


@router.delete("/app/orders/{order_id}")
def delete_order_ui(
    order_id: int,
    request: Request,
    db: DbSession,
    _current_user: CurrentUser,
    redirect_to_list: bool = False,
):
    try:
        delete_order(db, order_id)
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    if redirect_to_list:
        response = HTMLResponse("")
        response.headers["HX-Redirect"] = "/app/orders"
        return response

    response = render_alert(request, "Заявка удалена.", "success")
    response.headers["HX-Trigger"] = "refreshOrders"
    return response


# =========================
# Profile
# =========================

@router.get("/app/profile")
def profile_page(
    request: Request,
    current_user: CurrentUser,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "users/profile.html",
        {"user": current_user},
    )


@router.get("/app/profile/edit")
def edit_profile_form(
    request: Request,
    current_user: CurrentUser,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "users/_profile_edit.html",
        {"user": current_user},
    )


@router.get("/app/profile/summary")
def profile_summary(
    request: Request,
    current_user: CurrentUser,
) -> HTMLResponse:
    return render_profile_summary(request, current_user)


@router.post("/app/profile/edit")
def edit_profile_submit(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    email: str = Form(...),
    last_name: str | None = Form(default=None),
    first_name: str | None = Form(default=None),
    middle_name: str | None = Form(default=None),
):
    try:
        _, email_changed = update_profile(
            db=db,
            user_id=current_user.id,
            email=email,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    if email_changed:
        response = render_alert(
            request,
            "Профиль обновлён. Email изменён, войдите заново.",
            "success",
        )
        response.headers["HX-Redirect"] = "/app/logout"
        return response

    response = HTMLResponse("")
    response.headers["HX-Trigger"] = "refreshProfile"
    return response


@router.post("/app/profile/change-password")
def change_password_submit(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
):
    if new_password != new_password_confirm:
        return render_alert(
            request,
            "Новый пароль и подтверждение не совпадают.",
            "error",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 6:
        return render_alert(
            request,
            "Новый пароль должен быть не короче 6 символов.",
            "error",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        change_user_password(
            db=db,
            user_id=current_user.id,
            current_password=current_password,
            new_password=new_password,
        )
    except HTTPException as exc:
        return render_http_error_alert(request, exc)

    return render_alert(request, "Пароль успешно изменён.", "success")


# =========================
# Users (admin only)
# =========================

@router.get("/app/users")
def users_page(
    request: Request,
    _admin_user: AdminUser,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "users/page.html",
        {},
    )


@router.get("/app/users/table")
def users_table(
    request: Request,
    db: DbSession,
    _admin_user: AdminUser,
) -> HTMLResponse:
    return render_users_table_partial(request, db)


@router.get("/app/users/{user_id}/edit")
def edit_user_form(
    user_id: int,
    request: Request,
    db: DbSession,
    _admin_user: AdminUser,
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return render_alert(
            request,
            "Пользователь не найден.",
            "error",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        request,
        "users/_edit.html",
        {"user": user},
    )


@router.post("/app/users/create")
def create_user_ui(
    request: Request,
    db: DbSession,
    _admin_user: AdminUser,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    last_name: str | None = Form(default=None),
    first_name: str | None = Form(default=None),
    middle_name: str | None = Form(default=None),
):
    try:
        create_user(
            db=db,
            email=email,
            password=password,
            role=role,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
        )
    except HTTPException as exc:
        return render_hx_alert(
            request,
            text=str(exc.detail),
            kind="error",
            target="#create-user-result",
        )

    response = templates.TemplateResponse(
        request,
        "users/_create_result.html",
        {},
    )
    response.headers["HX-Trigger"] = "refreshUsers"
    return response


@router.post("/app/users/{user_id}/edit")
def edit_user_submit(
    user_id: int,
    request: Request,
    db: DbSession,
    _admin_user: AdminUser,
    email: str = Form(...),
    role: str = Form(...),
    last_name: str | None = Form(default=None),
    first_name: str | None = Form(default=None),
    middle_name: str | None = Form(default=None),
):
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
        return render_hx_alert(
            request,
            text="Пользователь не найден.",
            kind="error",
            target="#user-edit-modal",
        )
    except HTTPException as exc:
        return render_hx_alert(
            request,
            text=str(exc.detail),
            kind="error",
            target="#user-edit-modal",
        )

    response = HTMLResponse("")
    response.headers["HX-Trigger"] = "refreshUsers"
    return response


@router.post("/app/users/{user_id}/toggle-active")
def toggle_user_active_ui(
    user_id: int,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
):
    try:
        user = toggle_user_active(
            db=db,
            user_id=user_id,
            current_user_id=current_admin.id,
        )
    except HTTPException as exc:
        return render_hx_alert(
            request,
            text=str(exc.detail),
            kind="error",
            target="#users-alert",
        )

    response = render_hx_alert(
        request,
        text="Пользователь активирован." if user.is_active else "Пользователь деактивирован.",
        kind="success",
        target="#users-alert",
    )
    response.headers["HX-Trigger"] = "refreshUsers"
    return response


@router.delete("/app/users/{user_id}")
def delete_user_ui(
    user_id: int,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
):
    try:
        delete_user(
            db=db,
            user_id=user_id,
            current_user_id=current_admin.id,
        )
    except HTTPException as exc:
        return render_hx_alert(
            request,
            text=str(exc.detail),
            kind="error",
            target="#users-alert",
        )

    response = render_hx_alert(
        request,
        text="Пользователь удалён.",
        kind="success",
        target="#users-alert",
    )
    response.headers["HX-Trigger"] = "refreshUsers"
    return response