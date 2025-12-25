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

    # Calculate Gross Profit from Sales
    # Profit = (SaleItem.price - Product.buy_price) * Quantity
    # We need to iterate perfectly or use a smart query. Iterating is safer for complex logic MVP.
    gross_sales_profit = 0.0
    total_cogs = 0.0
    
    sale_items_query = db.query(SaleItem).join(Sale).filter(
        and_(Sale.created_at >= start_date, Sale.created_at <= end_date)
    ).all()

    for item in sale_items_query:
        # Check if product exists (it should)
        buy_price = float(item.product.buy_price) if item.product and item.product.buy_price else 0.0
        sell_price = float(item.price)
        qty = float(item.quantity)
        
        cogs_per_item = buy_price * qty
        total_cogs += cogs_per_item

        profit_per_item = (sell_price - buy_price) * qty
        gross_sales_profit += profit_per_item

    # --- 2. Refund Metrics (Negative) ---
    # Query all refunds in the period
    refunds_in_period = db.query(Refund).filter(
        and_(Refund.created_at >= start_date, Refund.created_at <= end_date)
    ).all()

    total_refunded_amount = 0.0
    for refund in refunds_in_period:
        total_refunded_amount += float(refund.total_refund_amount)

    # Calculate "Lost Profit" from Refunds and Cost of Returns
    # Lost Profit = (RefundItem.refund_price - Product.buy_price) * Quantity
    lost_profit = 0.0
    cogs_returned = 0.0
    
    refund_items_query = db.query(RefundItem).join(Refund).filter(
        and_(Refund.created_at >= start_date, Refund.created_at <= end_date)
    ).all()

    for item in refund_items_query:
        buy_price = float(item.product.buy_price) if item.product and item.product.buy_price else 0.0
        refund_price = float(item.refund_price)
        qty = float(item.quantity)
        
        # This is the profit we originally made but now have to give back (or lose)
        lost_profit_per_item = (refund_price - buy_price) * qty
        lost_profit += lost_profit_per_item
        
        cogs_returned += buy_price * qty

    # --- 3. Expenses ---
    expenses_query = db.query(Expense).filter(
        and_(Expense.created_at >= start_date, Expense.created_at <= end_date)
    ).all()
    
    total_expenses = 0.0
    for expense in expenses_query:
        total_expenses += float(expense.amount)

    # --- 4. Final Aggregation ---
    net_revenue = gross_sales_revenue - total_refunded_amount
    
    # Net Profit = (Gross Sales Profit - Lost Profit) - Expenses
    net_profit = (gross_sales_profit - lost_profit) - total_expenses

    return {
        "period": period_label,
        "total_revenue": Decimal(net_revenue), # Cast back to Decimal for Schema
        "total_cogs": Decimal(total_cogs - cogs_returned), # Net COGS
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
