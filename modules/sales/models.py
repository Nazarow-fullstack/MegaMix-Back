from sqlalchemy import Float, DateTime, func, ForeignKey, Numeric, String,Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db_config import Base

class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_debt: Mapped[bool] = mapped_column(Boolean, default=False)
    client = relationship("modules.clients.models.Client")
    seller = relationship("modules.auth.models.User")
    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    sale: Mapped["Sale"] = relationship(back_populates="items")
    product = relationship("modules.inventory.models.Product")

class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"))
    total_refund_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sale: Mapped["Sale"] = relationship("Sale")
    created_by = relationship("modules.auth.models.User")
    items: Mapped[list["RefundItem"]] = relationship(back_populates="refund")

class RefundItem(Base):
    __tablename__ = "refund_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    refund_id: Mapped[int] = mapped_column(ForeignKey("refunds.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    refund_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    refund: Mapped["Refund"] = relationship(back_populates="items")
    product = relationship("modules.inventory.models.Product")
    