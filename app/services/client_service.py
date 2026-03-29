from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client


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