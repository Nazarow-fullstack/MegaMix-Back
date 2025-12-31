from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db_config import get_db
from modules.auth.dependencies import get_current_active_user, require_manager, require_admin
from modules.auth.models import User

from . import service
from .models import Client
from .schemas import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
    PaymentCreate, 
    PaymentRead,
    ClientHistoryItem
)

router = APIRouter()

@router.post("/clients", response_model=ClientRead)
def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.create_client(db=db, client=client)

@router.get("/clients", response_model=List[ClientRead])
def read_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.get_clients(db=db, skip=skip, limit=limit, search=search)

@router.get("/clients/{client_id}", response_model=ClientRead)
def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.post("/payments", response_model=PaymentRead)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.add_payment(db=db, payment=payment, user=current_user)

@router.get("/clients/{client_id}/history", response_model=List[ClientHistoryItem])
def get_client_history(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.get_client_history(db=db, client_id=client_id)
    return service.get_client_history(db=db, client_id=client_id)

@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.update_client(db=db, client_id=client_id, data=client_data)

@router.delete("/clients/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service.delete_client(db=db, client_id=client_id)
    return {"detail": "Client deleted successfully"}
