from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, time
from decimal import Decimal
import calendar
from typing import Optional

from modules.sales.models import Sale, SaleItem, Refund, RefundItem
from modules.inventory.models import Product, StockMovement
from modules.expenses.models import Expense

def get_analytics(db: Session, period: str, month: Optional[int] = None, year: Optional[int] = None) -> dict:
    now = datetime.now()
    
    if month:
        target_year = year if year else now.year
        _, last_day = calendar.monthrange(target_year, month)
        
        start_date = datetime(target_year, month, 1, 0, 0, 0)
        end_date = datetime(target_year, month, last_day, 23, 59, 59)
        
        period_label = f"{calendar.month_name[month]} {target_year}"
    else:
        end_date = now
        
        if period == "today":
            start_date = datetime.combine(now.date(), time.min)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = datetime.combine(now.date(), time.min)
            
        period_label = period

    # --- 1. Sales Metrics (Gross) ---
    # Query all sales in the period
    sales_in_period = db.query(Sale).filter(
        and_(Sale.created_at >= start_date, Sale.created_at <= end_date)
    ).all()

    gross_sales_revenue = 0.0
    for sale in sales_in_period:
        gross_sales_revenue += float(sale.total_amount)

    sales_count = len(sales_in_period)

    # Calculate Gross Sales (Revenue)
    # Note: We no longer calculate COGS here because COGS is now recorded as an Expense (PURCHASE) when stock arrives.
    # So Profit = Revenue - Expenses.
    
    # We just need Revenue.
    # (Already calculated as gross_sales_revenue)

    # --- 2. Refund Metrics (Negative) ---
    # Query all refunds in the period
    refunds_in_period = db.query(Refund).filter(
        and_(Refund.created_at >= start_date, Refund.created_at <= end_date)
    ).all()

    total_refunded_amount = 0.0
    for refund in refunds_in_period:
        total_refunded_amount += float(refund.total_refund_amount)

    # --- 3. Expenses ---
    expenses_query = db.query(Expense).filter(
        and_(Expense.created_at >= start_date, Expense.created_at <= end_date)
    ).all()
    
    total_expenses = 0.0
    for expense in expenses_query:
        total_expenses += float(expense.amount)

    # --- 4. Final Aggregation ---
    net_revenue = gross_sales_revenue - total_refunded_amount
    
    # Net Profit = Revenue - Expenses
    # Expenses now include "PURCHASE" (COGS)
    net_profit = net_revenue - total_expenses

    return {
        "period": period_label,
        "total_revenue": Decimal(net_revenue), 
        "total_cogs": Decimal(0), # Deprecated concept in this view, or we could sum PURCHASE expenses specifically if needed.
        "total_refunds": Decimal(total_refunded_amount),
        "total_profit": Decimal(net_profit),
        "total_expenses": Decimal(total_expenses),
        "sales_count": sales_count
    }

def get_monthly_stock_report(db: Session, month: int, year: int) -> list[dict]:
    # 1. Determine the end of the requested month
    _, last_day = calendar.monthrange(year, month)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # 2. Get all products (current state)
    products = db.query(Product).all()
    
    # 3. Get all stock movements that happened AFTER the period
    #    We rely on the fact that StockMovement.change_amount is the signed delta (+ or -)
    future_movements = db.query(StockMovement).filter(
        StockMovement.created_at > end_date
    ).all()
    
    # 4. Aggregate deltas per product
    product_deltas = {}
    for movement in future_movements:
        if movement.product_id not in product_deltas:
            product_deltas[movement.product_id] = 0.0
        product_deltas[movement.product_id] += float(movement.change_amount)
        
    # 5. Build the report by backtracking
    #    Historical Qty = Current Qty - Sum(Changes after date)
    results = []
    for p in products:
        delta = product_deltas.get(p.id, 0.0)
        historical_qty = float(p.quantity) - delta
        
        results.append({
            "product_id": p.id,
            "name": p.name,
            "unit": p.unit,
            "historical_quantity": historical_qty
        })
        
    return results

def get_sales_by_product(db: Session, period: str, month: Optional[int] = None, year: Optional[int] = None) -> list[dict]:
    now = datetime.now()
    
    if month:
        target_year = year if year else now.year
        _, last_day = calendar.monthrange(target_year, month)
        
        start_date = datetime(target_year, month, 1, 0, 0, 0)
        end_date = datetime(target_year, month, last_day, 23, 59, 59)
    else:
        end_date = now
        
        if period == "today":
            start_date = datetime.combine(now.date(), time.min)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = datetime.combine(now.date(), time.min)

    results = db.query(
        Product.id,
        Product.name,
        Product.unit,
        func.sum(SaleItem.quantity).label("total_quantity"),
        func.sum(SaleItem.quantity * SaleItem.price).label("total_revenue")
    ).select_from(SaleItem)\
    .join(Sale, Sale.id == SaleItem.sale_id)\
    .join(Product, Product.id == SaleItem.product_id)\
    .filter(and_(Sale.created_at >= start_date, Sale.created_at <= end_date))\
    .group_by(Product.id)\
    .order_by(func.sum(SaleItem.quantity).desc())\
    .all()

    return [
        {
            "product_id": r.id,
            "product_name": r.name,
            "unit": r.unit,
            "total_quantity": float(r.total_quantity or 0),
            "total_revenue": Decimal(r.total_revenue or 0)
        }
        for r in results
    ]
