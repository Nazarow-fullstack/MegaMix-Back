import sys
import os
from datetime import datetime
from decimal import Decimal

# Add root to python path
sys.path.append(os.getcwd())

from db_config import SessionLocal, Base, engine
from modules.inventory.models import Product, StockMovement, MovementType
from modules.inventory.schemas import ProductCreate, StockMovementCreate
from modules.inventory.service import create_product, process_stock_movement
from modules.expenses.models import Expense, ExpenseCategory
from modules.sales.schemas import SaleCreate, SaleItemCreate
from modules.sales.service import create_sale
from modules.auth.models import User, UserRole

def verify():
    db = SessionLocal()
    try:
        # 1. Create a partial test user (Seller)
        print("--- 1. Setting up User ---")
        user = db.query(User).filter(User.username == "test_seller").first()
        if not user:
            user = User(username="test_seller", hashed_password="pw", role=UserRole.WORKER, is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
        print(f"User: {user.username} (ID: {user.id})")

        # 2. Create Product
        print("\n--- 2. Creating Product ---")
        # Ensure unique name
        p_name = f"TestProduct_{datetime.now().timestamp()}"
        product_data = ProductCreate(
            name=p_name,
            unit="pcs",
            items_per_pack=10,
            buy_price=50.0,
            recommended_price=100.0, # Recommended
            min_stock_level=5
        )
        product = create_product(db, product_data)
        print(f"Product Created: {product.name} (Buy: {product.buy_price}, Rec: {product.recommended_price})")

        # DEBUG: Check Enum
        print(f"DEBUG: ExpenseCategory.PURCHASE = {ExpenseCategory.PURCHASE!r}")
        print(f"DEBUG: ExpenseCategory.PURCHASE.value = {ExpenseCategory.PURCHASE.value!r}")
        
        # DEBUG: Check DB Enum
        from sqlalchemy import text
        result = db.execute(text("SELECT unnest(enum_range(NULL::expensecategory))")).fetchall()
        print(f"DEBUG: DB ExpenseCategory Enum Values: {[r[0] for r in result]}")

        # 3. Add Stock (IN) -> Expect Auto-Expense
        print("\n--- 3. Adding Stock (IN) ---")
        # Adding 10 items. Cost = 10 * 50 = 500.
        movement_data = StockMovementCreate(
            product_id=product.id,
            change_amount=10,
            type=MovementType.IN,
            comment="Initial Stock"
        )
        process_stock_movement(db, movement_data, user)
        
        # Verify Expense
        expense = db.query(Expense).filter(
            Expense.category == ExpenseCategory.PURCHASE, 
            Expense.description.ilike(f"%{product.name}%")
        ).order_by(Expense.id.desc()).first()
        
        if expense and expense.amount == 500:
            print(f"SUCCESS: Auto-Expense Created! Amount: {expense.amount} (Expected 500.00)")
        else:
            print(f"FAILURE: Auto-Expense not found or incorrect amount. Found: {expense.amount if expense else 'None'}")

        # 4. Process Sale with Custom Price
        print("\n--- 4. Processing Sale (Manual Price) ---")
        # Selling 2 items at 120 (Recommended was 100). Total = 240.
        sale_data = SaleCreate(
            paid_amount=Decimal(240),
            items=[
                SaleItemCreate(product_id=product.id, quantity=2, sold_price=Decimal(120))
            ]
        )
        sale = create_sale(db, sale_data, user)
        print(f"Sale Created: Total Amount {sale.total_amount}")
        
        if sale.total_amount == 240:
             print("SUCCESS: Sold price respected (Total = 240).")
        else:
             print(f"FAILURE: Total Amount {sale.total_amount} != 240.")

        # 5. Check Analytics (Profit)
        # Revenue = 240. Expenses = 500. Net Profit = 240 - 500 = -260.
        print("\n--- 5. Checking Analytics ---")
        from modules.analytics.service import get_analytics
        analytics = get_analytics(db, "today")
        
        # Note: Analytics aggregates ALL data, so specific values might be hard to isolate if DB is dirty.
        # But we can check if total_expenses >= 500 and total_revenue >= 240.
        print(f"Analytics Today: Revenue={analytics['total_revenue']}, Expenses={analytics['total_expenses']}, Profit={analytics['total_profit']}")
        
        # 6. Check Profile
        print("\n--- 6. Checking User Profile ---")
        from modules.auth.router import read_user_profile
        # We can't mock Depends easily here without overrides, but we can call logic manually or via router if we mock deps.
        # Let's just recreate the logic manually since we have the code.
        from modules.sales.models import Sale
        sales = db.query(Sale).filter(Sale.seller_id == user.id).all()
        count = len(sales)
        amount = sum(float(s.total_amount) for s in sales)
        print(f"User Stats: Count={count}, Amount={amount}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify()
