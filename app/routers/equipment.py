from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.equipment import EquipmentCreate, EquipmentResponse
from app.services.equipment_service import (
    create_equipment,
    get_all_equipment,
    get_equipment_by_id,
)

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment_endpoint(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
):
    return create_equipment(
        db=db,
        name=data.name,
        client_id=data.client_id,
        model=data.model,
        serial_number=data.serial_number,
        manufacturer=data.manufacturer,
    )


@router.get("/", response_model=list[EquipmentResponse])
def get_equipment_endpoint(db: Session = Depends(get_db)):
    return get_all_equipment(db)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id_endpoint(equipment_id: int, db: Session = Depends(get_db)):
    return get_equipment_by_id(db, equipment_id)