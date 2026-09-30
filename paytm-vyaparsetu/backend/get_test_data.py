import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

from db.session import SessionLocal
from db.models import Merchant, Customer, Distributor, InvoiceLineItem

def get_sample_data():
    db = SessionLocal()
    try:
        # Get a merchant
        merchant = db.query(Merchant).first()
        if not merchant:
            print("No merchants found in the database.")
            return

        merchant_id = merchant.merchant_id
        print(f"Merchant ID: {merchant_id}")
        
        # Get a customer for this merchant
        customer = db.query(Customer).filter(Customer.merchant_id == merchant_id).first()
        if customer:
            print(f"Sample Customer: {customer.display_name}")
            
        # Get a distributor for this merchant
        distributor = db.query(Distributor).filter(Distributor.merchant_id == merchant_id).first()
        if distributor:
            print(f"Sample Distributor: {distributor.name}")
            
        # Get an SKU for this merchant
        from db.models import Invoice
        item = db.query(InvoiceLineItem.sku).join(Invoice).filter(Invoice.merchant_id == merchant_id).first()
        if item:
            print(f"Sample SKU: {item.sku}")
            
    finally:
        db.close()

if __name__ == "__main__":
    get_sample_data()
