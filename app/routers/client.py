from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientResponse
from app.services.client_service import (
    create_client,
    get_all_clients,
    get_client_by_id,
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client_endpoint(
    data: ClientCreate,
    db: Session = Depends(get_db),
):
    return create_client(
        db=db,
        name=data.name,
        contact_person=data.contact_person,
        phone=data.phone,
        email=data.email,
        address=data.address,
        notes=data.notes,
    )


@router.get("/", response_model=list[ClientResponse])
def get_clients_endpoint(db: Session = Depends(get_db)):
    return get_all_clients(db)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_by_id_endpoint(client_id: int, db: Session = Depends(get_db)):
    return get_client_by_id(db, client_id)