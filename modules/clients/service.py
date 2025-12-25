from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import Client, Payment
from .schemas import ClientCreate, PaymentCreate
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
