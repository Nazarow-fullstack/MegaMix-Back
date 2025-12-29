from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date, time

from .models import Expense
from .schemas import ExpenseCreate, ExpenseUpdate
from modules.auth.models import User

from core.utils import get_date_range

def create_expense(db: Session, expense_data: ExpenseCreate, user: User) -> Expense:
    db_expense = Expense(
        amount=expense_data.amount,
        category=expense_data.category,
        description=expense_data.description,
        created_by_id=user.id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def get_expenses(
    db: Session, 
    period: str = "all", 
    month: Optional[int] = None, 
    year: Optional[int] = None
) -> List[Expense]:
    start_date, end_date = get_date_range(period, month, year)
    
    query = db.query(Expense).filter(and_(Expense.created_at >= start_date, Expense.created_at <= end_date))
    return query.order_by(Expense.created_at.desc()).all()

def delete_expense(db: Session, expense_id: int) -> bool:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense:
        db.delete(expense)
        db.commit()
        return True
    return False

def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate) -> Optional[Expense]:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return None

    if expense_data.amount is not None:
        expense.amount = expense_data.amount
    if expense_data.category is not None:
        expense.category = expense_data.category
    if expense_data.description is not None:
        expense.description = expense_data.description

    db.commit()
    db.refresh(expense)
    return expense
