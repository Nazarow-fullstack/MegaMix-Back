from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime

from enum import Enum

class TransactionType(str, Enum):
    sale = "sale"
    payment = "payment"

class ClientBase(BaseModel):
    full_name: str
    phone: str

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None

class ClientRead(ClientBase):
    id: int
    total_debt: Decimal
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(BaseModel):
    client_id: int
    amount: Decimal
    description: Optional[str] = None

class PaymentRead(BaseModel):
    id: int
    client_id: int
    amount: Decimal
    description: Optional[str] = None
    created_at: datetime
    performed_by_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ClientHistoryItem(BaseModel):
    id: int
    type: TransactionType
    amount: Decimal
    date: datetime
    description: Optional[str] = None
