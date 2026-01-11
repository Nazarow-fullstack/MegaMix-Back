from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from .models import UserRole

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: UserRole

class UserLogin(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserProfile(UserRead):
    total_sales_count: int
    total_sales_revenue: float # Using float for Pydantic compatibility with Numeric
    month_sales_revenue: float


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
