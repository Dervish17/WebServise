from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse
from app.services.client_service import (
    create_client,
    get_all_clients,
    get_client_by_id,
)

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    dependencies=[Depends(get_current_user)],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client_endpoint(
    data: ClientCreate,
    db: DbSession,
    _manager_or_admin: Annotated[
        User, Depends(require_roles(UserRole.admin, UserRole.manager))
    ],
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
def get_clients_endpoint(db: DbSession):
    return get_all_clients(db)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_by_id_endpoint(client_id: int, db: DbSession):
    return get_client_by_id(db, client_id)