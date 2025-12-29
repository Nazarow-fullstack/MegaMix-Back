from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

class AnalyticsResponse(BaseModel):
    period: str
    total_revenue: Decimal
    total_expenses: Decimal
    total_cogs: Decimal
    total_refunds: Decimal
    total_profit: Optional[Decimal] = None
    sales_count: int

class StockReportItem(BaseModel):
    product_id: int
    name: str
    unit: str
    historical_quantity: float

class ProductSalesSummary(BaseModel):
    product_id: int
    product_name: str
    unit: str
    total_quantity: float
    total_revenue: Decimal
