import sys
import os

# Reconfigure stdout for UTF-8 compatibility on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path so script can be run from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import (
    generate_merchant_id,
    generate_customer_id,
    generate_txn_id,
    generate_outbox_id,
    TxnType,
    LedgerSource,
    OutboxStatus,
    OutboxEventType,
)
from db.session import SessionLocal
from db.models import Merchant, Customer, LedgerTransaction, OutboxEvent


def seed_demo_data():
    """
    Populates sample demo data (merchant, customer, credit transaction, outbox event)
    using the master schema ORM models and core ID generators idempotently.
    """
    db = SessionLocal()
    try:
        phone = "+919876543210"
        merchant = db.query(Merchant).filter_by(phone=phone).first()
        if not merchant:
            print("[1/3] Creating sample merchant...")
            merchant_id = generate_merchant_id()
            merchant = Merchant(
                merchant_id=merchant_id,
                shop_name="Gupta Provision Store",
                owner_name="Ramesh Gupta",
                phone=phone,
                cognee_dataset=f"merchant_{merchant_id}",
            )
            db.add(merchant)
            db.flush()
            print(f"  -> Created Merchant: {merchant.shop_name} (ID: {merchant_id})")
        else:
            merchant_id = merchant.merchant_id
            print(f"[1/3] Found existing Merchant: {merchant.shop_name} (ID: {merchant_id})")

        print("[2/3] Resolving customer (Suresh)...")
        canonical_key = "suresh"
        customer = (
            db.query(Customer)
            .filter_by(merchant_id=merchant_id, canonical_key=canonical_key)
            .first()
        )
        if not customer:
            customer_id = generate_customer_id()
            customer = Customer(
                customer_id=customer_id,
                merchant_id=merchant_id,
                display_name="Suresh",
                canonical_key=canonical_key,  # Normalized canonical key for identity resolution
                phone="+919812345678",
            )
            db.add(customer)
            db.flush()
            print(f"  -> Created Customer: {customer.display_name} (ID: {customer_id})")
        else:
            customer_id = customer.customer_id
            print(f"  -> Found existing Customer: {customer.display_name} (ID: {customer_id})")

        print("[3/3] Logging sample credit transaction & outbox event...")
        txn_id = generate_txn_id()
        ledger_entry = LedgerTransaction(
            txn_id=txn_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount=240.00,
            txn_type=TxnType.CREDIT_ADDED,
            items=["Dahi 200g", "Refined Oil"],
            source=LedgerSource.VOICE,
            extraction_confidence=0.92,
        )
        db.add(ledger_entry)

        outbox_id = generate_outbox_id()
        outbox_event = OutboxEvent(
            event_id=outbox_id,
            merchant_id=merchant_id,
            event_type=OutboxEventType.CREDIT_ADDED,
            payload={
                "txn_id": txn_id,
                "customer_id": customer_id,
                "amount": 240.00,
                "txn_type": "CREDIT_ADDED",
            },
            status=OutboxStatus.PENDING,
        )
        db.add(outbox_event)

        db.commit()
        print(f"  -> Created Ledger Txn: {txn_id} (Amount: INR 240.00)")
        print(f"  -> Created Outbox Event: {outbox_id} (Status: PENDING)")

        print("\nDemo data seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
