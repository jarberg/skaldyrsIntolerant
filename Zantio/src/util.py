import sys

from datetime import date
from datetime import timedelta

def month_bounds(year: int, month: int) -> (date, date):
    """
    Returns (first_day, last_day) for the given year/month.
    """
    first = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last = next_month - timedelta(days=1)
    return first, last


def get_latest_date() -> (date, date):
    # Determine period to invoice: default = previous month
    today = date.today()
    if len(sys.argv) == 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        # previous month
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1
    period_start, period_end = month_bounds(year, month)
    print(f"Generating invoices for period {period_start} to {period_end} (YYYY-MM) = {year}-{month:02d}")

    return period_start, period_end

