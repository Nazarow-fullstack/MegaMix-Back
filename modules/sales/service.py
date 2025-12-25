from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import Sale, SaleItem, Refund, RefundItem
from .schemas import SaleCreate, RefundCreate
from modules.inventory.models import Product, StockMovement, MovementType
from modules.clients.models import Client
from modules.auth.models import User

def create_sale(db: Session, sale_data: SaleCreate, seller: User) -> Sale:
    """
    Creates a sale atomically:
    1. Validates stock and debt requirements.
    2. Deducts stock (StockMovement + Product.quantity).
    3. Calculates totals.
    4. Updates Client debt if needed.
    5. Creates Sale and SaleItems.
    """
    
    # 1. Fetch all products and validate existence/stock
    total_amount = Decimal(0)
    sale_items_data = []
    
    # To prevent deadlocks or race conditions, we should lock these rows, 
    # but for simplicity in this MVP, we'll fetch and check. 
    # Proper way: SELECT FOR UPDATE.
    
    for item in sale_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        if product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product '{product.name}'")
        
        item_total = Decimal(product.sell_price) * Decimal(item.quantity)
        total_amount += item_total
        
        sale_items_data.append({
            "product": product,
            "quantity": item.quantity,
            "price": product.sell_price
        })

    # 2. Check Debt Rules
    if sale_data.paid_amount < total_amount and not sale_data.client_id:
        raise HTTPException(
            status_code=400, 
            detail="Client must be specified when paying less than total amount (credit sale)"
        )

    # 3. Create Sale Record
    db_sale = Sale(
        client_id=sale_data.client_id,
        seller_id=seller.id,
        total_amount=total_amount,
        paid_amount=sale_data.paid_amount
    )
    db.add(db_sale)
    db.flush() # Flush to get ID if needed, but primarily to ensure constraint validity

    # 4. Process Items (Add SaleItem, Deduct Stock)
    for data in sale_items_data:
        product = data["product"]
        quantity = data["quantity"]
        price = data["price"]
        
        # Add SaleItem
        db_sale_item = SaleItem(
            sale_id=db_sale.id,
            product_id=product.id,
            quantity=quantity,
            price=price
        )
        db.add(db_sale_item)
        
        # Stock Movement (OUT)
        db_movement = StockMovement(
            product_id=product.id,
            change_amount= -quantity, # Deduct
            type=MovementType.OUT,
            performed_by_id=seller.id,
            comment=f"Sale #{db_sale.id}"
        )
        db.add(db_movement)
        
        # Update Product Quantity
        product.quantity -= quantity

    # 5. Update Client Debt
    if sale_data.client_id:
        client = db.query(Client).filter(Client.id == sale_data.client_id).with_for_update().first()
        if not client:
             raise HTTPException(status_code=400, detail="Client not found")
        
        debt_increase = total_amount - sale_data.paid_amount
        # Note: If they pay MORE (paid_amount > total_amount), debt DECREASES (change_amount is negative).
        # This logic works: debt += (500 - 600) => debt += -100.
        
        if client.total_debt + debt_increase < 0:
             client.total_debt = 0
        else:
             client.total_debt += debt_increase

    db.commit()
    db.refresh(db_sale)
    return db_sale

def create_refund(db: Session, sale_id: int, refund_data: RefundCreate, user: User) -> Refund:
    """
    Creates a refund for a specific sale:
    1. Validates items exist in original sale.
    2. Calculates refund amount.
    3. Increases Stock (IN).
    4. Decreases Client Debt (if client exists).
    5. Records Refund.
    """
    # 1. Fetch Sale
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # 2. Validate Items & Calculate Total
    total_refund_amount = Decimal(0)
    refund_items_data = []

    for item in refund_data.items:
        # Find original sale item
        sale_item = db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.product_id == item.product_id
        ).first()

        if not sale_item:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found in this sale")
        
        if item.quantity > sale_item.quantity:
             # Simple validation: cannot return more than bought (ignoring previous refunds for MVP)
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot refund {item.quantity}. Only sold {sale_item.quantity} of Product {item.product_id}"
            )
        
        refund_price = sale_item.price
        item_total = Decimal(refund_price) * Decimal(item.quantity)
        total_refund_amount += item_total
        
        refund_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "refund_price": refund_price
        })

    # 3. Create Refund Record
    db_refund = Refund(
        sale_id=sale_id,
        total_refund_amount=total_refund_amount,
        reason=refund_data.reason,
        created_by_id=user.id
    )
    db.add(db_refund)
    db.flush()

    # 4. Process Items (Add RefundItem, Return Stock)
    for data in refund_items_data:
        # Add RefundItem
        db_refund_item = RefundItem(
            refund_id=db_refund.id,
            product_id=data["product_id"],
            quantity=data["quantity"],
            refund_price=data["refund_price"]
        )
        db.add(db_refund_item)
        
        # Stock Movement (IN)
        db_movement = StockMovement(
            product_id=data["product_id"],
            change_amount=data["quantity"], # Positive for IN
            type=MovementType.IN,
            performed_by_id=user.id,
            comment=f"Refund for Sale #{sale_id}"
        )
        db.add(db_movement)
        
        # Update Product Quantity
        product = db.query(Product).filter(Product.id == data["product_id"]).with_for_update().first()
        if product:
             product.quantity += data["quantity"]

    # 5. Update Client Debt (Only if client exists)
    if sale.client_id:
        client = db.query(Client).filter(Client.id == sale.client_id).with_for_update().first()
        if client:
             # Reduce debt (or increase credit), but don't go negative
             if client.total_debt - total_refund_amount < 0:
                 client.total_debt = 0
             else:
                 client.total_debt -= total_refund_amount

    db.commit()
    db.refresh(db_refund)
    db.commit()
    db.refresh(db_refund)
    return db_refund

def get_refunds(db: Session, skip: int = 0, limit: int = 100) -> list[Refund]:
    return db.query(Refund).offset(skip).limit(limit).all()

def get_product_sales_history(db: Session, product_id: int, skip: int = 0, limit: int = 100):
    # Query SaleItems for the product, join Sale to get date/client/seller
    # We select specific columns to avoid N+1 if possible, but ORM loading is fine for this scale.
    
    results = db.query(SaleItem, Sale, Client, User)\
        .join(Sale, SaleItem.sale_id == Sale.id)\
        .outerjoin(Client, Sale.client_id == Client.id)\
        .join(User, Sale.seller_id == User.id)\
        .filter(SaleItem.product_id == product_id)\
        .order_by(Sale.created_at.desc())\
        .offset(skip).limit(limit).all()
        
    history = []
    for item, sale, client, seller in results:
        history.append({
            "sale_id": sale.id,
            "sale_date": sale.created_at,
            "client_name": client.full_name if client else "Anonymous",
            "quantity": item.quantity,
            "unit_price": item.price,
            "seller_name": seller.username,
            "total": Decimal(item.quantity) * item.price
        })
        
    return history
