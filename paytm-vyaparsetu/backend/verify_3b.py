import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal
from db.repositories import merchants_repo, customers_repo

def main():
    db = SessionLocal()
    try:
        # Create a test merchant
        # we append a random string to phone to avoid unique constraint if we run multiple times
        import random
        rand_suffix = str(random.randint(1000, 9999))
        merchant = merchants_repo.create_merchant(db, "Test Store", "Test Owner", f"+9190000{rand_suffix}")
        print(f"Created merchant: {merchant.merchant_id}")

        # Create customer "Suresh"
        customer1 = customers_repo.get_or_create(db, merchant.merchant_id, "Suresh")
        print(f"Created customer 1: {customer1.customer_id} (name: {customer1.display_name}, canonical: {customer1.canonical_key})")

        # Create customer "suresh"
        customer2 = customers_repo.get_or_create(db, merchant.merchant_id, " suresh  ")
        print(f"Created customer 2: {customer2.customer_id} (name: {customer2.display_name}, canonical: {customer2.canonical_key})")

        if customer1.customer_id == customer2.customer_id:
            print("SUCCESS! Canonical deduplication works. customer1 and customer2 are exactly the same record.")
        else:
            print("FAILURE! Duplicate customers were created.")
            
        # Clean up
        db.delete(customer1)
        db.delete(merchant)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    main()
