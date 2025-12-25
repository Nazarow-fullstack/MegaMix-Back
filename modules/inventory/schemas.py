from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional
from decimal import Decimal
from datetime import datetime
from .models import MovementType

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    unit: str
    min_stock_level: Optional[float] = 10.0

class ProductCreate(ProductBase):
    buy_price: Decimal
    sell_price: Decimal

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    buy_price: Optional[Decimal] = None
    sell_price: Optional[Decimal] = None
    min_stock_level: Optional[float] = None

# Response Schemas for different roles

class ProductReadWorker(ProductBase):
    id: int
    quantity: float
    
    model_config = ConfigDict(from_attributes=True)

class ProductReadManager(ProductReadWorker):
    sell_price: Decimal

class ProductReadAdmin(ProductReadManager):
    buy_price: Decimal

class StockMovementCreate(BaseModel):
    product_id: int
    change_amount: float
    type: MovementType
    comment: Optional[str] = None

class StockMovementRead(BaseModel):
    id: int
    created_at: datetime
    type: MovementType
    change_amount: float
    comment: Optional[str] = None
    performed_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
