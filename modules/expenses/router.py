from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from db_config import get_db
from modules.auth.dependencies import require_manager, require_admin
from modules.auth.models import User
from . import service
from .schemas import ExpenseCreate, ExpenseRead

router = APIRouter(tags=["Expenses"])

@router.post("/", response_model=ExpenseRead)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.create_expense(db=db, expense_data=expense, user=current_user)

@router.get("/", response_model=List[ExpenseRead])
def read_expenses(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return service.get_expenses(db=db, start_date=start_date, end_date=end_date)

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    success = service.delete_expense(db=db, expense_id=expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")
