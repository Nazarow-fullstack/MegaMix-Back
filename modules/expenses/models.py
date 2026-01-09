from enum import Enum
from sqlalchemy import String, DateTime, func, ForeignKey, Numeric, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db_config import Base

class ExpenseCategory(str, Enum):
    SALARY = "salary"
    RENT = "rent"
    UTILITIES = "utilities"
    TAXES = "taxes"
    PURCHASE = "purchase"
    OTHER = "other"

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(SAEnum(ExpenseCategory), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_by = relationship("modules.auth.models.User")
