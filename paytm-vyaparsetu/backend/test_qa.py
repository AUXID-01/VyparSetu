import os
import sys
from pydantic import ValidationError
from datetime import date
sys.path.append(os.path.join(os.path.dirname(__file__)))

from services.qa_tools import (
    DailyBalanceQuery,
    SkuPriceTrendQuery,
    CustomerDueQuery,
    DateRange,
    normalize_date_range,
    resolve_sku
)

print("--- Running Validation Tests ---")

try:
    q = DailyBalanceQuery(target_date="2026-09-29")
    print("Test M (target_date valid): PASS", type(q.target_date))
except ValidationError:
    print("Test M (target_date valid): FAIL")

try:
    q = DailyBalanceQuery(target_date="invalid")
    print("Test N (target_date invalid): FAIL")
except ValidationError:
    print("Test N (target_date invalid): PASS")

try:
    q = SkuPriceTrendQuery(item_name="Dahi", days=60)
    print("Test O1 (days 60): PASS")
except ValidationError:
    print("Test O1 (days 60): FAIL")

try:
    q = SkuPriceTrendQuery(item_name="Dahi", days=0)
    print("Test O (days 0): FAIL")
except ValidationError:
    print("Test O (days 0): PASS")

try:
    q = SkuPriceTrendQuery(item_name="Dahi", days=366)
    print("Test P (days 366): FAIL")
except ValidationError:
    print("Test P (days 366): PASS")

print("--- DateRange Tests ---")
start, end = normalize_date_range(DateRange.LAST_7_DAYS, reference_date=date(2026, 9, 29))
print(f"LAST_7_DAYS from 2026-09-29: {start} to {end}")

print("All static tests complete.")
