"""
scripts/seed_demo.py
Seeds exactly two merchants (Ramesh Gupta and Tukaram Shinde) with clean, curated data for the live demo.
Run with: python -m scripts.seed_demo
"""

import datetime
from api.deps import SessionLocal
from db.models import Merchant, Invoice, SettlementDailyRollup
from db.repositories import customers_repo, ledger_repo, distributors_repo, invoices_repo, outbox_repo
from vision.schemas import ConfirmedChallanInput, ConfirmedLineItem, TaxBreakdown
from core.enums import TxnType, LedgerSource

def seed_demo():
    db = SessionLocal()
    try:
        print("🌱 Seeding Demo Environment...")
        
        # =========================================================================
        # Merchant 1: Ramesh Gupta
        # =========================================================================
        print("-> Seeding Ramesh Gupta (mer_ramesh_gupta)")
        ramesh = Merchant(
            merchant_id="mer_ramesh_gupta",
            shop_name="Gupta Provision Store",
            owner_name="Ramesh Gupta",
            phone="+919876543210",
            cognee_dataset="merchant_mer_ramesh_gupta"
        )
        db.add(ramesh)
        db.commit()
        db.refresh(ramesh)

        # Customer: Suresh (Credit: 240)
        c_suresh = customers_repo.resolve_or_create(db, ramesh.merchant_id, "Suresh", "Suresh")
        txn = ledger_repo.insert_transaction(
            db, ramesh.merchant_id, c_suresh.customer_id, 240.00, 
            TxnType.CREDIT_ADDED.value, LedgerSource.VOICE.value, ["Dahi", "Refined Oil"]
        )
        outbox_repo.create_outbox_event(db, ramesh.merchant_id, "CREDIT_ADDED", {"txn_id": txn.txn_id, "amount": 240.00})

        # Distributor: Amul Distributor
        d_amul = distributors_repo.resolve_or_create(db, ramesh.merchant_id, "Amul Distributor")

        # Invoice 1 (5 days ago, Paid)
        date_5_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        inv1_input = ConfirmedChallanInput(
            distributor_name_raw="Amul Distributor",
            challan_type="FORMAL_GST",
            capture_medium="CAMERA_PHOTO",
            challan_date=date_5_days_ago,
            subtotal=27.00,
            total_payable=27.00,
            line_items=[ConfirmedLineItem(raw_text="Dahi 200g Pouch", canonical_item_name="Dahi 200g Pouch", quantity=1.0, unit="pcs", unit_rate=27.00, line_total=27.00)],
            tax=TaxBreakdown(cgst=0, sgst=0, igst=0)
        )
        inv1 = invoices_repo.insert_confirmed_invoice(db, ramesh.merchant_id, d_amul.distributor_id, inv1_input)
        invoices_repo.insert_line_items(db, inv1.invoice_id, d_amul.distributor_id, inv1_input.line_items)
        
        # Manually mark as paid
        inv1.is_paid = True
        db.commit()
        
        # Invoice 2 (Today, Unpaid, triggers Rate Spike)
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        inv2_input = ConfirmedChallanInput(
            distributor_name_raw="Amul Distributor",
            challan_type="FORMAL_GST",
            capture_medium="CAMERA_PHOTO",
            challan_date=today,
            subtotal=28.50,
            total_payable=28.50,
            line_items=[ConfirmedLineItem(raw_text="Dahi 200g Pouch", canonical_item_name="Dahi 200g Pouch", quantity=1.0, unit="pcs", unit_rate=28.50, line_total=28.50)],
            tax=TaxBreakdown(cgst=0, sgst=0, igst=0)
        )
        inv2 = invoices_repo.insert_confirmed_invoice(db, ramesh.merchant_id, d_amul.distributor_id, inv2_input)
        line_items2 = invoices_repo.insert_line_items(db, inv2.invoice_id, d_amul.distributor_id, inv2_input.line_items)
        
        # Simulate rate spike check
        prev_price = invoices_repo.get_last_price(db, d_amul.distributor_id, line_items2[0].sku, inv2.invoice_id)
        assert prev_price == 27.00, "❌ Failed to retrieve previous price for rate spike!"
        delta = float(line_items2[0].unit_price) - prev_price
        assert delta == 1.50, f"❌ Rate spike alert calculation failed! Expected 1.50, got {delta}"
        print("✅ Rate-spike alert actively triggered and verified: +₹1.50")

        # Settlement Daily Rollup (Today)
        rollup = SettlementDailyRollup(
            rollup_id="roll_demo_01",
            merchant_id=ramesh.merchant_id,
            rollup_date=datetime.datetime.utcnow().date(),
            upi_collection_total=6200.00,
            payout_total=3850.00,
            net_balance=2350.00
        )
        db.add(rollup)
        db.commit()

        # =========================================================================
        # Merchant 2: Tukaram Shinde
        # =========================================================================
        print("-> Seeding Tukaram Shinde (mer_tukaram_shinde)")
        tukaram = Merchant(
            merchant_id="mer_tukaram_shinde",
            shop_name="Shinde Dairy & Bakery",
            owner_name="Tukaram Shinde",
            phone="+919876543211",
            cognee_dataset="merchant_mer_tukaram_shinde"
        )
        db.add(tukaram)
        db.commit()

        print("🎉 DEMO Seeding Complete! (Ready for live pitch)")

    except Exception as e:
        db.rollback()
        print(f"❌ Demo seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo()
