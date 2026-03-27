from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.equipment import Equipment


def create_equipment(
    db: Session,
    name: str,
    client_id: int,
    model: str | None = None,
    serial_number: str | None = None,
    manufacturer: str | None = None,
) -> Equipment:
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    equipment = Equipment(
        name=name,
        model=model,
        serial_number=serial_number,
        manufacturer=manufacturer,
        client_id=client_id,
    )

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    return equipment


def get_all_equipment(db: Session) -> list[type[Equipment]]:
    return db.query(Equipment).order_by(Equipment.id.desc()).all()


def get_equipment_by_id(db: Session, equipment_id: int) -> type[Equipment]:
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment