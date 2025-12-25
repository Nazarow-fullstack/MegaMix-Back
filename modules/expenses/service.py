from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date, time

from .models import Expense
from .schemas import ExpenseCreate
from modules.auth.models import User

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
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
) -> List[Expense]:
    query = db.query(Expense)
    
    if start_date and end_date:
        query = query.filter(and_(Expense.created_at >= start_date, Expense.created_at <= end_date))
    
    return query.all()

def delete_expense(db: Session, expense_id: int) -> bool:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense:
        db.delete(expense)
        db.commit()
        return True
    return False
