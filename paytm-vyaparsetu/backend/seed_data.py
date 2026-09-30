import os
import sys
import uuid
from datetime import date, datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__)))

from db.session import SessionLocal
from db.models import Merchant, Customer, Distributor, Invoice, InvoiceLineItem, SettlementDailyRollup, LedgerTransaction
from core.enums import TxnType

def seed_database():
    db = SessionLocal()
    try:
        # Get the target merchant
        merchant = db.query(Merchant).filter(Merchant.merchant_id == 'mer_e249b2').first()
        if not merchant:
            print("Target merchant not found. Seeding aborted.")
            return

        print("Seeding recent data for merchant:", merchant.merchant_id)
        
        today = date.today()
        
        # 1. Seed Settlement Daily Rollups for the past 7 days
        for i in range(7):
            target_date = today - timedelta(days=i)
            existing = db.query(SettlementDailyRollup).filter_by(merchant_id=merchant.merchant_id, rollup_date=target_date).first()
            if not existing:
                rollup = SettlementDailyRollup(
                    rollup_id=f"rol_{uuid.uuid4().hex[:6]}",
                    merchant_id=merchant.merchant_id,
                    rollup_date=target_date,
                    upi_collection_total=15000.00 + (i * 1200),
                    payout_total=8000.00 + (i * 500),
                    net_balance=7000.00 + (i * 700)
                )
                db.add(rollup)
        
        # 2. Add Recent Invoices and SKUs
        distributor = db.query(Distributor).filter_by(merchant_id=merchant.merchant_id).first()
        if distributor:
            # Invoice 1 (Today)
            inv1 = Invoice(
                invoice_id=f"inv_seed_{uuid.uuid4().hex[:6]}",
                merchant_id=merchant.merchant_id,
                distributor_id=distributor.distributor_id,
                invoice_date=today,
                total_amount=5000.00,
                is_paid=True
            )
            db.add(inv1)
            db.flush()
            
            # Line items for invoice 1
            item1 = InvoiceLineItem(
                line_item_id=f"lin_seed_{uuid.uuid4().hex[:6]}",
                invoice_id=inv1.invoice_id,
                distributor_id=distributor.distributor_id,
                sku="Amul Dahi 500g",
                quantity=10,
                unit_price=45.00,
                raw_text="Amul Dahi 500g",
                unit="pcs"
            )
            item2 = InvoiceLineItem(
                line_item_id=f"lin_seed_{uuid.uuid4().hex[:6]}",
                invoice_id=inv1.invoice_id,
                distributor_id=distributor.distributor_id,
                sku="Apple Normal 1kg",
                quantity=20,
                unit_price=120.00,
                raw_text="Apple Normal 1kg",
                unit="kg"
            )
            db.add_all([item1, item2])
            
            # Invoice 2 (1 month ago) - for Price Trend
            inv2 = Invoice(
                invoice_id=f"inv_seed_{uuid.uuid4().hex[:6]}",
                merchant_id=merchant.merchant_id,
                distributor_id=distributor.distributor_id,
                invoice_date=today - timedelta(days=30),
                total_amount=4500.00,
                is_paid=True
            )
            db.add(inv2)
            db.flush()
            
            # Line items for invoice 2 (older, cheaper prices)
            item3 = InvoiceLineItem(
                line_item_id=f"lin_seed_{uuid.uuid4().hex[:6]}",
                invoice_id=inv2.invoice_id,
                distributor_id=distributor.distributor_id,
                sku="Amul Dahi 500g",
                quantity=10,
                unit_price=40.00,  # Price increased from 40 to 45
                raw_text="Amul Dahi 500g",
                unit="pcs"
            )
            item4 = InvoiceLineItem(
                line_item_id=f"lin_seed_{uuid.uuid4().hex[:6]}",
                invoice_id=inv2.invoice_id,
                distributor_id=distributor.distributor_id,
                sku="Apple Normal 1kg",
                quantity=20,
                unit_price=100.00, # Price increased from 100 to 120
                raw_text="Apple Normal 1kg",
                unit="kg"
            )
            db.add_all([item3, item4])
            
        # 3. Add Ledger Transactions
        customer = db.query(Customer).filter_by(merchant_id=merchant.merchant_id).first()
        if customer:
            txn1 = LedgerTransaction(
                txn_id=f"txn_seed_{uuid.uuid4().hex[:6]}",
                merchant_id=merchant.merchant_id,
                customer_id=customer.customer_id,
                amount=1500.00,
                txn_type=TxnType.CREDIT_ADDED.value,
                source="MANUAL",
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            txn2 = LedgerTransaction(
                txn_id=f"txn_seed_{uuid.uuid4().hex[:6]}",
                merchant_id=merchant.merchant_id,
                customer_id=customer.customer_id,
                amount=500.00,
                txn_type=TxnType.CREDIT_PAID.value,
                source="MANUAL",
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.add_all([txn1, txn2])
            
        db.commit()
        print("Database seeded successfully with recent records!")
        
    except Exception as e:
        db.rollback()
        print("Error during seeding:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
