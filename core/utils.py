from datetime import datetime, timedelta, time
import calendar
from typing import Optional, Tuple

def get_date_range(period: str = "all", month: Optional[int] = None, year: Optional[int] = None) -> Tuple[datetime, datetime]:
    """
    Calculates the start and end datetime based on the given period or specific month/year.
    """
    now = datetime.now()
    
    if month:
        target_year = year if year else now.year
        try:
            _, last_day = calendar.monthrange(target_year, month)
            start_date = datetime(target_year, month, 1, 0, 0, 0)
            end_date = datetime(target_year, month, last_day, 23, 59, 59)
        except (ValueError, IndexError):
            # Fallback for invalid month
            start_date = datetime.combine(now.date(), time.min)
            end_date = now
    else:
        # Default end date is now for relative periods
        end_date = now
        
        if period == "today":
            start_date = datetime.combine(now.date(), time.min)
            end_date = datetime.combine(now.date(), time.max)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            # Last 30 days
            start_date = now - timedelta(days=30)
        elif period == "year":
             start_date = datetime(now.year, 1, 1, 0, 0, 0)
        elif period == "all":
            # Return a range that covers likely everything or specific start
            start_date = datetime.min
        else:
             # Default fallback
            start_date = datetime.min

    return start_date, end_date
