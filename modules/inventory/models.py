from enum import Enum
from sqlalchemy import String, Float, Enum as SAEnum, DateTime, func, ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db_config import Base

class MovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)  # kg, pcs, etc.
    items_per_pack: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # How many items in 1 pack
    buy_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False) # Secret
    recommended_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0) 
    min_stock_level: Mapped[float] = mapped_column(Float, default=10.0)
    
    movements: Mapped[list["StockMovement"]] = relationship(back_populates="product")

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    change_amount: Mapped[float] = mapped_column(Float, nullable=False) # +50 or -10
    type: Mapped[MovementType] = mapped_column(SAEnum(MovementType), nullable=False)
    performed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="movements")
    performed_by = relationship("modules.auth.models.User")
