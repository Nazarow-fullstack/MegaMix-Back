from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db_config import get_db
from modules.auth.dependencies import require_manager, require_admin
from modules.auth.models import User

from . import service
from .models import Sale
from .schemas import (
    SaleCreate, 
    SaleRead,
    RefundCreate,
    SaleRead,
    RefundCreate,
    RefundRead,
    ProductSaleHistoryItem
)

router = APIRouter()

@router.post("/sales", response_model=SaleRead)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.create_sale(db=db, sale_data=sale, seller=current_user)

@router.get("/sales", response_model=List[SaleRead])
def read_sales(
    skip: int = 0,
    limit: int = 100,
    period: str = "all",
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.get_sales(db=db, skip=skip, limit=limit, period=period, month=month, year=year)

@router.get("/sales/{sale_id}", response_model=SaleRead)
def read_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.post("/sales/{sale_id}/refund", response_model=RefundRead)
def refund_sale(
    sale_id: int,
    refund: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.create_refund(db=db, sale_id=sale_id, refund_data=refund, user=current_user)

@router.get("/refunds", response_model=List[RefundRead])
def read_refunds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.get_refunds(db=db, skip=skip, limit=limit)

@router.get("/products/{product_id}/history", response_model=List[ProductSaleHistoryItem])
def get_product_sales_history(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.get_product_sales_history(db, product_id, skip, limit)
