from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from .models import Client, Payment
from .schemas import ClientCreate, PaymentCreate, ClientHistoryItem, TransactionType, ClientUpdate
from modules.sales.models import Sale
from modules.auth.models import User

def create_client(db: Session, client: ClientCreate) -> Client:
    # Check for existing phone
    db_client = db.query(Client).filter(Client.phone == client.phone).first()
    if db_client:
        raise HTTPException(status_code=400, detail="Client with this phone already exists")
        
    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_clients(db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
    return db.query(Client).filter(Client.is_active == True).offset(skip).limit(limit).all()

def add_payment(db: Session, payment: PaymentCreate, user: User) -> Payment:
    """
    Adds a payment and reduces client debt atomically.
    """
    client = db.query(Client).filter(Client.id == payment.client_id).with_for_update().first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create payment record
    db_payment = Payment(
        client_id=payment.client_id,
        amount=payment.amount,
        description=payment.description,
        performed_by_id=user.id
    )
    
    # Update client debt (Debt decreases when payment is made)
    if client.total_debt - payment.amount < 0:
        client.total_debt = 0
    else:
        client.total_debt -= payment.amount
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_client_history(db: Session, client_id: int) -> List[ClientHistoryItem]:
    # Check if client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Step A: Get Payments
    payments = db.query(Payment).filter(Payment.client_id == client_id).all()
    history_items = []
    
    for payment in payments:
        history_items.append(ClientHistoryItem(
            id=payment.id,
            type=TransactionType.payment,
            amount=payment.amount,
            date=payment.created_at,
            description=payment.description or "Payment"
        ))

    # Step B: Get Sales
    sales = db.query(Sale).filter(Sale.client_id == client_id).all()
    
    for sale in sales:
        history_items.append(ClientHistoryItem(
            id=sale.id,
            type=TransactionType.sale,
            amount=sale.total_amount,
            date=sale.created_at,
            description=f"Sale #{sale.id}"
        ))

    # Step C & D: Sort by date descending
    history_items.sort(key=lambda x: x.date, reverse=True)
    
    history_items.sort(key=lambda x: x.date, reverse=True)
    
    return history_items

def update_client(db: Session, client_id: int, data: ClientUpdate) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if data.phone and data.phone != client.phone:
        existing = db.query(Client).filter(Client.phone == data.phone).first()
        if existing:
            raise HTTPException(status_code=400, detail="Client with this phone already exists")

    if data.full_name:
        client.full_name = data.full_name
    if data.phone:
        client.phone = data.phone

    db.add(client)
    db.commit()
    db.refresh(client)
    return client

def delete_client(db: Session, client_id: int):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.is_active = False
    db.commit()
    return True
