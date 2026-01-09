from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: float
    sold_price: Decimal

class SaleCreate(BaseModel):
    client_id: Optional[int] = None
    paid_amount: Decimal
    items: List[SaleItemCreate]

class ProductSimpleRead(BaseModel):
    id: int
    name: str
    unit: str
    model_config = ConfigDict(from_attributes=True)

class SaleItemRead(BaseModel):
    id: int
    product_id: int
    quantity: float
    price: Decimal
    product: ProductSimpleRead
    
    model_config = ConfigDict(from_attributes=True)

class SaleRead(BaseModel):
    id: int
    client_id: Optional[int]
    seller_id: int
    total_amount: Decimal
    paid_amount: Decimal
    items: List[SaleItemRead]
    created_at: datetime
    estimated_profit: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class RefundItemCreate(BaseModel):
    product_id: int
    quantity: float

class RefundCreate(BaseModel):
    items: List[RefundItemCreate]
    reason: Optional[str] = None

class RefundItemRead(BaseModel):
    id: int
    product_id: int
    quantity: float
    refund_price: Decimal
    
    model_config = ConfigDict(from_attributes=True)

class RefundRead(BaseModel):
    id: int
    sale_id: int
    total_refund_amount: Decimal
    items: List[RefundItemRead]
    created_at: datetime
    reason: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class ProductSaleHistoryItem(BaseModel):
    sale_id: int
    sale_date: datetime
    client_name: str
    quantity: float
    unit_price: Decimal
    seller_name: str
    total: Decimal
    
    model_config = ConfigDict(from_attributes=True)
