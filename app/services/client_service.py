from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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


def get_all_clients(db: Session) -> list[type[Client]]:
    return db.query(Client).order_by(Client.id.desc()).all()


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