import sys
import os
sys.path.append(os.getcwd())

try:
    from modules.analytics.schemas import StockReportItem
    from modules.analytics.service import get_monthly_stock_report
    from modules.analytics.router import router
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
