from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentResponse

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/", response_model=EquipmentResponse)
def create_equipment(data: EquipmentCreate, db: Session = Depends(get_db)):
    equipment = Equipment(
        name=data.name,
        client_id=data.client_id
    )

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    return equipment


@router.get("/", response_model=list[EquipmentResponse])
def get_equipment(db: Session = Depends(get_db)):
    return db.query(Equipment).all()