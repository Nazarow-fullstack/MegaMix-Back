from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from sqlalchemy import and_
from .models import Sale, SaleItem, Refund, RefundItem
from .schemas import SaleCreate, RefundCreate
from modules.inventory.models import Product, StockMovement, MovementType
from modules.clients.models import Client
from modules.auth.models import User
from core.utils import get_date_range

def get_sales(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    period: str = "all", 
    month: int = None, 
    year: int = None
) -> list[Sale]:
    start_date, end_date = get_date_range(period, month, year)
    
    query = db.query(Sale).options(
        joinedload(Sale.seller),
        joinedload(Sale.client),
        joinedload(Sale.items).joinedload(SaleItem.product) # Load items and products
    ).filter(and_(Sale.created_at >= start_date, Sale.created_at <= end_date))
    
    sales = query.order_by(Sale.created_at.desc()).offset(skip).limit(limit).all()

    for sale in sales:
        sale.seller_name = sale.seller.username if sale.seller else "Unknown"
        sale.client_name = sale.client.full_name if sale.client else None
        
        profit = 0.0
        for item in sale.items:
            buy_price = float(item.product.buy_price) if item.product and item.product.buy_price else 0.0
            sell_price = float(item.price)
            quantity = float(item.quantity)
            profit += (sell_price - buy_price) * quantity
        
        sale.estimated_profit = profit

    return sales

def get_sale(db: Session, sale_id: int):
    sale = db.query(Sale).options(
        joinedload(Sale.seller),
        joinedload(Sale.client)
    ).filter(Sale.id == sale_id).first()
    
    if sale:
        sale.seller_name = sale.seller.username if sale.seller else "Unknown"
        sale.client_name = sale.client.full_name if sale.client else None
    return sale

def create_sale(db: Session, sale_data: SaleCreate, seller: User) -> Sale:
    # 1. Validation & Total Calculation
    total_amount = Decimal(0)
    sale_items_data = []

    for item_data in sale_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item_data.product_id} not found")
        
        if product.quantity < item_data.quantity:
             raise HTTPException(status_code=400, detail=f"Insufficient stock for product '{product.name}'")
        
        sold_price = item_data.sold_price
        
        item_total = sold_price * Decimal(item_data.quantity)
        total_amount += item_total
        
        sale_items_data.append({
            "product": product,
            "quantity": item_data.quantity,
            "price": sold_price
        })

    # 2. Check Debt Rules
    is_debt = False
    if sale_data.paid_amount < total_amount:
        if not sale_data.client_id:
             raise HTTPException(status_code=400, detail="Cannot sell with debt to Anonymous customer. Full payment required.")
        is_debt = True
    
    # 3. Create Sale Record
    db_sale = Sale(
        client_id=sale_data.client_id,
        seller_id=seller.id,
        total_amount=float(total_amount),
        paid_amount=float(sale_data.paid_amount),
        is_debt=is_debt
    )
    db.add(db_sale)
    db.flush()

    # 4. Process Items (Add SaleItem, Deduct Stock)
    for data in sale_items_data:
        product = data["product"]
        quantity = data["quantity"]
        price = data["price"]

        # Sale Item
        db_item = SaleItem(
            sale_id=db_sale.id,
            product_id=product.id,
            quantity=quantity,
            price=float(price)
        )
        db.add(db_item)

        # Stock Movement (OUT)
        movement = StockMovement(
            product_id=product.id,
            change_amount=-quantity,
            type=MovementType.OUT,
            comment=f"Sale #{db_sale.id}",
            performed_by_id=seller.id
        )
        db.add(movement)
        
        # Update Product Quantity
        product.quantity -= quantity

    # 5. Update Client Debt
    if sale_data.client_id:
        client = db.query(Client).filter(Client.id == sale_data.client_id).with_for_update().first()
        if not client:
             raise HTTPException(status_code=400, detail="Client not found")
        
        # Calculate change as float
        debt_change = float(total_amount) - float(sale_data.paid_amount)
        
        # Cast existing debt to float for calculation
        current_debt = float(client.total_debt)
        
        if current_debt + debt_change < 0:
             client.total_debt = 0.0
        else:
             client.total_debt = current_debt + debt_change
        db.add(client)

    db.commit()
    db.refresh(db_sale)
    
    # 6. ВАЖНО: Исправили переменную на 'seller'
    db_sale.seller_name = seller.username
    
    return db_sale

def create_refund(db: Session, sale_id: int, refund_data: RefundCreate, user: User) -> Refund:
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    total_refund_amount = Decimal(0)
    refund_items_data = []

    for item in refund_data.items:
        sale_item = db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.product_id == item.product_id
        ).first()

        if not sale_item:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found in this sale")
        
        if item.quantity > sale_item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot refund {item.quantity}. Only sold {sale_item.quantity}"
            )
        
        refund_price = sale_item.price
        item_total = Decimal(refund_price) * Decimal(item.quantity)
        total_refund_amount += item_total
        
        refund_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "refund_price": refund_price
        })

    db_refund = Refund(
        sale_id=sale_id,
        total_refund_amount=float(total_refund_amount),
        reason=refund_data.reason,
        created_by_id=user.id
    )
    db.add(db_refund)
    db.flush()

    for data in refund_items_data:
        db_refund_item = RefundItem(
            refund_id=db_refund.id,
            product_id=data["product_id"],
            quantity=data["quantity"],
            refund_price=float(data["refund_price"])
        )
        db.add(db_refund_item)
        
        db_movement = StockMovement(
            product_id=data["product_id"],
            change_amount=data["quantity"],
            type=MovementType.IN,
            performed_by_id=user.id,
            comment=f"Refund for Sale #{sale_id}"
        )
        db.add(db_movement)
        
        product = db.query(Product).filter(Product.id == data["product_id"]).with_for_update().first()
        if product:
             product.quantity += data["quantity"]

    if sale.client_id:
        client = db.query(Client).filter(Client.id == sale.client_id).with_for_update().first()
        if client:
             if client.total_debt - float(total_refund_amount) < 0:
                 client.total_debt = 0
             else:
                 client.total_debt -= float(total_refund_amount)

    db.commit()
    db.refresh(db_refund)
    return db_refund

def get_refunds(db: Session, skip: int = 0, limit: int = 100) -> list[Refund]:
    return db.query(Refund).offset(skip).limit(limit).all()

def get_product_sales_history(db: Session, product_id: int, skip: int = 0, limit: int = 100):
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
            "total": Decimal(item.quantity) * Decimal(item.price)
        })
        
    return history