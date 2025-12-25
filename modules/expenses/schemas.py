from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from .models import ExpenseCategory

class ExpenseCreate(BaseModel):
    amount: float
    category: ExpenseCategory
    description: Optional[str] = None

class ExpenseRead(BaseModel):
    id: int
    amount: Decimal
    category: ExpenseCategory
    description: Optional[str]
    created_at: datetime
    created_by_id: int
    
    model_config = ConfigDict(from_attributes=True)
