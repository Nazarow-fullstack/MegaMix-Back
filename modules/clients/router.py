from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db_config import get_db
from modules.auth.dependencies import require_manager
from modules.auth.models import User

from . import service
from .models import Client, Payment
from .schemas import (
    ClientCreate, 
    ClientRead, 
    PaymentCreate, 
    PaymentRead
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return db.query(Client).offset(skip).limit(limit).all()

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
