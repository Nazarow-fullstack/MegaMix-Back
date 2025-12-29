from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db_config import get_db
from modules.auth.dependencies import get_current_active_user, require_admin, require_manager
from modules.auth.models import User, UserRole

from . import service
from .models import Product
from .schemas import (
    ProductCreate,
    ProductReadAdmin,
    ProductReadManager,
    ProductReadWorker,
    StockMovementCreate,
    StockMovementRead,
    ProductUpdate
)

router = APIRouter()

@router.post("/products", response_model=ProductReadAdmin)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return service.create_product(db=db, product=product)

@router.get("/products", response_model=List[Union[ProductReadAdmin, ProductReadManager, ProductReadWorker]])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    products = db.query(Product).offset(skip).limit(limit).all()
    
    # Selecting the schema based on role is tricky with response_model=Union because FastAPI
    # might try to validate against the first matching one or all.
    # To strictly enforce which fields are returned, we can return the objects and 
    # let FastAPI filter based on response_model if we could specify it dynamically.
    # BUT FastAPI doesn't support dynamic response_schema easily per request.
    # Solution: We manually exclude fields or return specific Pydantic models.
    # However, to be type-safe with the Union, we need to convert them explicitly.
    
    if current_user.role == UserRole.ADMIN:
        return [ProductReadAdmin.model_validate(p) for p in products]
    elif current_user.role == UserRole.MANAGER:
        return [ProductReadManager.model_validate(p) for p in products]
    else:
        return [ProductReadWorker.model_validate(p) for p in products]

@router.post("/movements")
def create_movement(
    movement: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == UserRole.WORKER:
        raise HTTPException(status_code=403, detail="Workers cannot modify stock")
        
    return service.process_stock_movement(db=db, movement=movement, user=current_user)

@router.get("/products/{product_id}/movements", response_model=List[StockMovementRead])
def read_product_movements(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return service.get_product_movements(db, product_id, skip, limit)

@router.put("/products/{product_id}", response_model=ProductReadAdmin)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    return service.update_product(db=db, product_id=product_id, data=product_data)

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    service.delete_product(db=db, product_id=product_id)
    return {"detail": "Product deleted successfully"}
