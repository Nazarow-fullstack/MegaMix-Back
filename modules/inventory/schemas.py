from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional
from decimal import Decimal
from .models import MovementType
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    unit: str
    items_per_pack: int = 1 # Добавили поле
    min_stock_level: Optional[float] = 10.0

class ProductCreate(ProductBase):
    buy_price: Decimal
    # Делаем цену продажи необязательной при создании
    recommended_price: Optional[Decimal] = None 

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    items_per_pack: Optional[int] = None
    buy_price: Optional[Decimal] = None
    recommended_price: Optional[Decimal] = None
    min_stock_level: Optional[float] = None

# --- Response Schemas ---

class ProductReadWorker(ProductBase):
    id: int
    quantity: float
    
    model_config = ConfigDict(from_attributes=True)

class ProductReadManager(ProductReadWorker):
    # Важно: делаем Optional, так как в базе может быть null
    recommended_price: Optional[Decimal] = None 

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