from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from enum import Enum
from typing import Optional

from db_config import get_db
from modules.auth.dependencies import get_current_active_user
from modules.auth.models import User, UserRole
from . import service
from .schemas import AnalyticsResponse, StockReportItem

router = APIRouter()

class PeriodEnum(str, Enum):
    today = "today"
    week = "week"
    month = "month"

@router.get("/stats", response_model=AnalyticsResponse)
def get_stats(
    period: PeriodEnum = Query(PeriodEnum.today),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by specific month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, description="Filter by specific year (e.g. 2024)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == UserRole.WORKER:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")
    
    data = service.get_analytics(db, period.value, month=month, year=year)
    
    # Hide profit for Managers
    if current_user.role == UserRole.MANAGER:
        data["total_profit"] = None
        
    return data

@router.get("/stock-report", response_model=list[StockReportItem])
def get_stock_report(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year (e.g. 2024)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == UserRole.WORKER:
        raise HTTPException(status_code=403, detail="Not authorized to view stock report")
        
    report = service.get_monthly_stock_report(db, month, year)
    return report
