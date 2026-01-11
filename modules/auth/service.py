from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func
from datetime import datetime, date
from .models import User
from .schemas import UserUpdate
from .security import get_password_hash
from jose import jwt, JWTError 
from core.config import settings 
# Import Sale model for stats
from modules.sales.models import Sale

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int):
    val = db.query(User).filter(User.id == user_id).first()
    if not val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return val

def update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    db_user.is_active = False
    
    
    db.commit()
    return db_user

def get_current_user_from_token(db: Session, token: str):

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
        
    return user

def get_user_profile_stats(db: Session, user_id: int):
    """
    Fetches user details and calculates sales statistics.
    """
    user = get_user_by_id(db, user_id)
    
    # Base query for user's sales
    query = db.query(Sale).filter(Sale.seller_id == user_id)
    
    # 1. Total Sales Count
    total_sales_count = query.count()
    
    # 2. Total Revenue
    # func.sum returns None if no rows match, so coalesce to 0
    total_revenue = db.query(func.sum(Sale.total_amount)).filter(Sale.seller_id == user_id).scalar() or 0.0
    
    # 3. Monthly Revenue
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    month_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.seller_id == user_id,
        Sale.created_at >= month_start
    ).scalar() or 0.0

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "total_sales_count": total_sales_count,
        "total_sales_revenue": total_revenue,
        "month_sales_revenue": month_revenue
    }