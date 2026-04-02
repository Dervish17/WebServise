from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.equipment import Equipment
from app.models.order import Order
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
from app.routers.ui_shared import render_alert, templates

router = APIRouter(tags=["ui"])


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
