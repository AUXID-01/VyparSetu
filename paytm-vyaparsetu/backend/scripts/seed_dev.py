"""
scripts/seed_dev.py
Seeds the dev environment with 3 merchants to test edge cases, dedup logic, and isolation.
Run with: python -m scripts.seed_dev
"""

from api.deps import SessionLocal
from db.repositories import merchants_repo, customers_repo, ledger_repo, distributors_repo, invoices_repo, outbox_repo
from db.models import OutboxEvent
from vision.schemas import ConfirmedChallanInput, ConfirmedLineItem, TaxBreakdown
from core.enums import TxnType, LedgerSource

def seed_dev():
    db = SessionLocal()
    try:
        print("🌱 Seeding Development Environment...")

        # =========================================================================
        # Merchant 1: Baseline Clean Store
        # =========================================================================
        print("-> Seeding Merchant 1: Baseline Clean Store")
        m1 = merchants_repo.create_merchant(db, "Baseline Clean Store", "Raju", "+919000000001")
        
        # Customers
        c1_1 = customers_repo.resolve_or_create(db, m1.merchant_id, "Amit", "Amit")
        c1_2 = customers_repo.resolve_or_create(db, m1.merchant_id, "Rahul", "Rahul")
        
        # Ledger Transactions
        for amount in [100.0, 200.0, 150.0]:
            txn = ledger_repo.insert_transaction(db, m1.merchant_id, c1_1.customer_id, amount, TxnType.CREDIT_ADDED.value, LedgerSource.VOICE.value)
            outbox_repo.create_outbox_event(db, m1.merchant_id, "CREDIT_ADDED", {"txn_id": txn.txn_id, "amount": amount})
        
        for amount in [500.0, 300.0]:
            txn = ledger_repo.insert_transaction(db, m1.merchant_id, c1_2.customer_id, amount, TxnType.CREDIT_ADDED.value, LedgerSource.VOICE.value)
            outbox_repo.create_outbox_event(db, m1.merchant_id, "CREDIT_ADDED", {"txn_id": txn.txn_id, "amount": amount})

        # Distributor
        d1 = distributors_repo.resolve_or_create(db, m1.merchant_id, "Amul Dairy")
        
        # Invoice 1 (Old Price)
        inv1_input = ConfirmedChallanInput(
            distributor_name_raw="Amul Dairy",
            challan_type="FORMAL_GST",
            capture_medium="CAMERA_PHOTO",
            challan_date="2026-09-01",
            subtotal=27.00,
            total_payable=27.00,
            line_items=[ConfirmedLineItem(raw_text="Dahi 200g Pouch", canonical_item_name="Dahi 200g Pouch", quantity=1.0, unit="pcs", unit_rate=27.00, line_total=27.00)],
            tax=TaxBreakdown(cgst=0, sgst=0, igst=0)
        )
        inv1 = invoices_repo.insert_confirmed_invoice(db, m1.merchant_id, d1.distributor_id, inv1_input)
        invoices_repo.insert_line_items(db, inv1.invoice_id, d1.distributor_id, inv1_input.line_items)
        outbox_repo.create_outbox_event(db, m1.merchant_id, "INVOICE_CREATED", {"invoice_id": inv1.invoice_id, "total_amount": 27.00})

        # Invoice 2 (New Price)
        inv2_input = ConfirmedChallanInput(
            distributor_name_raw="Amul Dairy",
            challan_type="FORMAL_GST",
            capture_medium="CAMERA_PHOTO",
            challan_date="2026-09-15",
            subtotal=28.50,
            total_payable=28.50,
            line_items=[ConfirmedLineItem(raw_text="Dahi 200g Pouch", canonical_item_name="Dahi 200g Pouch", quantity=1.0, unit="pcs", unit_rate=28.50, line_total=28.50)],
            tax=TaxBreakdown(cgst=0, sgst=0, igst=0)
        )
        inv2 = invoices_repo.insert_confirmed_invoice(db, m1.merchant_id, d1.distributor_id, inv2_input)
        invoices_repo.insert_line_items(db, inv2.invoice_id, d1.distributor_id, inv2_input.line_items)
        outbox_repo.create_outbox_event(db, m1.merchant_id, "INVOICE_CREATED", {"invoice_id": inv2.invoice_id, "total_amount": 28.50})


        # =========================================================================
        # Merchant 2: Dedup Stress Test Store
        # =========================================================================
        print("-> Seeding Merchant 2: Dedup Stress Test Store")
        m2 = merchants_repo.create_merchant(db, "Dedup Stress Test Store", "Pooja", "+919000000002")
        
        # Deduplication check for "Suresh"
        c2_1 = customers_repo.resolve_or_create(db, m2.merchant_id, "Suresh", "Suresh")
        c2_2 = customers_repo.resolve_or_create(db, m2.merchant_id, "suresh", "suresh")
        c2_3 = customers_repo.resolve_or_create(db, m2.merchant_id, " Suresh ", " Suresh ")
        
        assert c2_1.customer_id == c2_2.customer_id == c2_3.customer_id, "❌ Customer Deduplication Failed!"
        
        # Deduplication check for "Amul Distributor"
        d2_1 = distributors_repo.resolve_or_create(db, m2.merchant_id, "Amul Distributor")
        db.commit()
        d2_2 = distributors_repo.resolve_or_create(db, m2.merchant_id, "amul distributor")
        
        assert d2_1.distributor_id == d2_2.distributor_id, "❌ Distributor Deduplication Failed!"
        print("✅ Deduplication logic authentically exercised and passed.")

        # =========================================================================
        # Merchant 3: Cross-Merchant Isolation Store
        # =========================================================================
        print("-> Seeding Merchant 3: Cross-Merchant Isolation Store")
        m3 = merchants_repo.create_merchant(db, "Cross-Merchant Isolation Store", "Rohan", "+919000000003")
        
        # Exact same distributor and SKU as Merchant 1
        d3 = distributors_repo.resolve_or_create(db, m3.merchant_id, "Amul Dairy")
        assert d3.distributor_id != d1.distributor_id, "❌ Cross-Merchant Distributor Leakage Detected!"
        
        inv3_input = ConfirmedChallanInput(
            distributor_name_raw="Amul Dairy",
            challan_type="FORMAL_GST",
            capture_medium="CAMERA_PHOTO",
            challan_date="2026-09-01",
            subtotal=27.00,
            total_payable=27.00,
            line_items=[ConfirmedLineItem(raw_text="Dahi 200g Pouch", canonical_item_name="Dahi 200g Pouch", quantity=1.0, unit="pcs", unit_rate=27.00, line_total=27.00)],
            tax=TaxBreakdown(cgst=0, sgst=0, igst=0)
        )
        inv3 = invoices_repo.insert_confirmed_invoice(db, m3.merchant_id, d3.distributor_id, inv3_input)
        invoices_repo.insert_line_items(db, inv3.invoice_id, d3.distributor_id, inv3_input.line_items)
        outbox_repo.create_outbox_event(db, m3.merchant_id, "INVOICE_CREATED", {"invoice_id": inv3.invoice_id, "total_amount": 27.00})


        # =========================================================================
        # Verify Outbox Events
        # =========================================================================
        outbox_count = db.query(OutboxEvent).filter(OutboxEvent.status == "PENDING").count()
        assert outbox_count == 8, f"❌ Expected 8 pending outbox events, got {outbox_count}"
        print("✅ Outbox events authentically queued (status=PENDING).")
        print("🎉 DEV Seeding Complete!")

    except Exception as e:
        db.rollback()
        print(f"❌ Dev seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_dev()
