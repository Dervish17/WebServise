from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.normalization import (
    clean_optional_text,
    clean_required_text,
    normalize_optional_email,
)
from app.models.client import Client
from app.models.order import Order
from app.models.equipment import Equipment


def create_client(
    db: Session,
    name: str,
    contact_person: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    notes: str | None = None,
) -> Client:
    try:
        name = clean_required_text(name, "Название клиента")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    contact_person = clean_optional_text(contact_person)
    phone = clean_optional_text(phone)
    email = normalize_optional_email(email)
    address = clean_optional_text(address)
    notes = clean_optional_text(notes)

    client = Client(
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


def get_all_clients(
    db: Session,
    search: str | None = None,
    sort: str = "newest",
):
    query = db.query(Client)

    if search:
        search = search.strip()
        query = query.filter(
            (Client.name.ilike(f"%{search}%")) |
            (Client.contact_person.ilike(f"%{search}%")) |
            (Client.phone.ilike(f"%{search}%")) |
            (Client.email.ilike(f"%{search}%")) |
            (Client.address.ilike(f"%{search}%")) |
            (Client.notes.ilike(f"%{search}%"))
        )

    if sort == "oldest":
        query = query.order_by(Client.id.asc())
    elif sort == "name_asc":
        query = query.order_by(Client.name.asc())
    elif sort == "name_desc":
        query = query.order_by(Client.name.desc())
    else:
        query = query.order_by(Client.id.desc())

    return query.all()


def get_client_by_id(db: Session, client_id: int) -> type[Client]:
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    return client


def update_client(
    db: Session,
    client_id: int,
    name: str,
    contact_person: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    notes: str | None = None,
) -> Client:
    client = get_client_by_id(db, client_id)

    try:
        name = clean_required_text(name, "Название клиента")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    contact_person = clean_optional_text(contact_person)
    phone = clean_optional_text(phone)
    email = normalize_optional_email(email)
    address = clean_optional_text(address)
    notes = clean_optional_text(notes)

    client.name = name
    client.contact_person = contact_person
    client.phone = phone
    client.email = email
    client.address = address
    client.notes = notes

    db.commit()
    db.refresh(client)

    return client


def delete_client(db: Session, client_id: int) -> None:
    client = get_client_by_id(db, client_id)

    equipment_exists = (
        db.query(Equipment)
        .filter(Equipment.client_id == client_id)
        .first()
    )

    if equipment_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить клиента: у него есть оборудование",
        )

    order_exists = (
        db.query(Order)
        .filter(Order.client_id == client_id)
        .first()
    )

    if order_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить клиента: у него есть заявки",
        )

    db.delete(client)
    db.commit()