from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import Product, StockMovement, MovementType
from .schemas import ProductCreate, StockMovementCreate, ProductUpdate
from modules.auth.models import User
from modules.expenses.models import Expense, ExpenseCategory

def get_products(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Product]:
    query = db.query(Product)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
        
    return query.offset(skip).limit(limit).all()

def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def process_stock_movement(db: Session, movement: StockMovementCreate, user: User) -> StockMovement:
    """
    Unified function to handle stock movements.
    - IN: Adds quantity.
    - OUT: Subtracts quantity (validates sufficient stock).
    """
    product = db.query(Product).filter(Product.id == movement.product_id).with_for_update().first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    final_change_amount = movement.change_amount

    if movement.type == MovementType.OUT:
        if product.quantity < movement.change_amount:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        final_change_amount = -movement.change_amount
        product.quantity -= movement.change_amount
    elif movement.type == MovementType.IN:
        product.quantity += movement.change_amount
        
        # Auto-Expense Logic
        cost = Decimal(movement.change_amount) * Decimal(product.buy_price)
        description = f"Авто-закупка: {product.name} (Поступление)"
        
        expense = Expense(
            amount=cost,
            category=ExpenseCategory.PURCHASE,
            description=description,
            created_by_id=user.id
        )
        db.add(expense)
    else:
        # Fallback for other types
        product.quantity += movement.change_amount

    # Create movement record
    db_movement = StockMovement(
        product_id=movement.product_id,
        change_amount=final_change_amount,
        type=movement.type,
        comment=movement.comment,
        performed_by_id=user.id
    )
    
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    db.refresh(db_movement)
    return db_movement

def get_product_movements(db: Session, product_id: int, skip: int = 0, limit: int = 100):
    results = db.query(StockMovement, User)\
        .join(User, StockMovement.performed_by_id == User.id)\
        .filter(StockMovement.product_id == product_id)\
        .order_by(StockMovement.created_at.desc())\
        .offset(skip).limit(limit).all()
        
    movements = []
    for m, u in results:
        movements.append({
            "id": m.id,
            "created_at": m.created_at,
            "type": m.type,
            "change_amount": m.change_amount,
            "comment": m.comment,
            "performed_by_name": u.username
        })
    return movements

def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        db.delete(product)
        db.commit()
    except Exception as e:
        db.rollback()
        # likely integrity error if foreign keys exist and no cascade
        raise HTTPException(status_code=400, detail="Cannot delete product. It likely has associated stock movements or history.")