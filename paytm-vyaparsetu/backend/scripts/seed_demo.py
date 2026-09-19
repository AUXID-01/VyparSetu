"""
scripts/seed_demo.py

Seeds exactly the data judges will see. Every ID below is FIXED, not
randomly generated — this is a deliberate departure from core.ids'
normal random-hex generator, because demo data needs to be referenceable
by hand (login by phone number, look up a specific customer_id while
debugging on stage) across as many wipe+reseed cycles as you need.

Run with: python -m scripts.seed_demo
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from db.session import SessionLocal
from db.models import Merchant, Customer, Distributor, LedgerTransaction, Invoice, InvoiceLineItem, OutboxEvent, SettlementDailyRollup
import uuid

# Fixed imports to match core.enums
from core.enums import TxnType, LedgerSource as TxnSource, OutboxEventType as EventType

# ============================================================
# FIXED IDs — this is your login/reference sheet, keep it in sync
# with the printed table you hand to whoever's driving the demo.
# ============================================================

MER_GUPTA = "mer_gupta01"
MER_SHINDE = "mer_shinde01"

CUS_SURESH = "cus_suresh01"
CUS_PRIYA = "cus_priya01"
CUS_MANOJ = "cus_manoj01"
CUS_GANESH = "cus_ganesh01"
CUS_LATA = "cus_lata01"

DIS_AMUL = "dis_amul01"
DIS_BRITANNIA = "dis_britannia01"
DIS_LOCALDAIRY = "dis_localdairy01"


def seed():
    db = SessionLocal()
    try:
        # --------------------------------------------------------
        # MERCHANT 1 — Gupta Provision Store (the headline demo merchant)
        # --------------------------------------------------------
        _merchant(
            db, merchant_id=MER_GUPTA,
            shop_name="Gupta Provision Store", owner_name="Ramesh Gupta",
            phone="+919876500001", cognee_dataset=f"merchant_{MER_GUPTA}",
        )

        _customer(db, customer_id=CUS_SURESH, merchant_id=MER_GUPTA,
                  display_name="Suresh", canonical_key="suresh", phone="+919812345601")
        _customer(db, customer_id=CUS_PRIYA, merchant_id=MER_GUPTA,
                  display_name="Priya", canonical_key="priya", phone="+919812345602")
        _customer(db, customer_id=CUS_MANOJ, merchant_id=MER_GUPTA,
                  display_name="Manoj", canonical_key="manoj", phone="+919812345603")

        _distributor(db, distributor_id=DIS_AMUL, merchant_id=MER_GUPTA,
                     name="Amul Distributor", canonical_key="amul distributor",
                     upi_id="amuldistributor@icici")
        _distributor(db, distributor_id=DIS_BRITANNIA, merchant_id=MER_GUPTA,
                     name="Britannia Distributor", canonical_key="britannia distributor",
                     upi_id="britanniadist@hdfc")

        # ---- Ledger transactions
        _txn(db, MER_GUPTA, CUS_SURESH, 240.00, TxnType.CREDIT_ADDED, ["Dahi", "Refined Oil"], "2026-09-14")
        _txn(db, MER_GUPTA, CUS_SURESH, 150.00, TxnType.CREDIT_ADDED, ["Bread"], "2026-09-15")
        _txn(db, MER_GUPTA, CUS_SURESH, 100.00, TxnType.CREDIT_PAID, [], "2026-09-16")
        _txn(db, MER_GUPTA, CUS_PRIYA, 500.00, TxnType.CREDIT_ADDED, ["Rice", "Atta"], "2026-09-15")
        _txn(db, MER_GUPTA, CUS_MANOJ, 80.00, TxnType.CREDIT_ADDED, ["Milk"], "2026-09-14")
        _txn(db, MER_GUPTA, CUS_MANOJ, 80.00, TxnType.CREDIT_ADDED, ["Milk"], "2026-09-15")
        _txn(db, MER_GUPTA, CUS_MANOJ, 160.00, TxnType.CREDIT_PAID, [], "2026-09-16")

        # ---- Amul invoices
        _invoice(db, MER_GUPTA, DIS_AMUL, "2026-09-01", [("Dahi 200g pouch", 20, 27.00)])
        _invoice(db, MER_GUPTA, DIS_AMUL, "2026-09-08", [("Dahi 200g pouch", 20, 27.00)])
        _invoice(db, MER_GUPTA, DIS_AMUL, "2026-09-16", [("Dahi 200g pouch", 20, 28.50),
                                                           ("Amul Milk Crates", 10, 350.00)])

        # ---- Britannia invoices
        _invoice(db, MER_GUPTA, DIS_BRITANNIA, "2026-09-05", [("Bread 400g", 15, 42.00)])
        _invoice(db, MER_GUPTA, DIS_BRITANNIA, "2026-09-16", [("Bread 400g", 15, 42.00)])

        # ---- Settlement rollups
        _settlement(db, MER_GUPTA, "2026-09-14", upi=3100.00, payout=0.00, net=3100.00)
        _settlement(db, MER_GUPTA, "2026-09-15", upi=4800.00, payout=2200.00, net=2600.00)
        _settlement(db, MER_GUPTA, "2026-09-16", upi=6200.00, payout=3850.00, net=2350.00)

        # --------------------------------------------------------
        # MERCHANT 2 — Shinde Dairy & Bakery (the isolation-proof merchant)
        # --------------------------------------------------------
        _merchant(
            db, merchant_id=MER_SHINDE,
            shop_name="Shinde Dairy & Bakery", owner_name="Tukaram Shinde",
            phone="+919876500002", cognee_dataset=f"merchant_{MER_SHINDE}",
        )

        _customer(db, customer_id=CUS_GANESH, merchant_id=MER_SHINDE,
                  display_name="Ganesh", canonical_key="ganesh", phone="+919812345701")
        _customer(db, customer_id=CUS_LATA, merchant_id=MER_SHINDE,
                  display_name="Lata", canonical_key="lata", phone="+919812345702")

        _distributor(db, distributor_id=DIS_LOCALDAIRY, merchant_id=MER_SHINDE,
                     name="Local Dairy Co-op", canonical_key="local dairy co-op",
                     upi_id="localdairy@ybl")

        _txn(db, MER_SHINDE, CUS_GANESH, 300.00, TxnType.CREDIT_ADDED, ["Milk", "Eggs"], "2026-09-16")
        _txn(db, MER_SHINDE, CUS_LATA, 150.00, TxnType.CREDIT_ADDED, ["Bread"], "2026-09-16")

        _invoice(db, MER_SHINDE, DIS_LOCALDAIRY, "2026-09-10", [("Eggs (tray of 30)", 5, 210.00)])
        _invoice(db, MER_SHINDE, DIS_LOCALDAIRY, "2026-09-16", [("Eggs (tray of 30)", 5, 210.00)])

        _settlement(db, MER_SHINDE, "2026-09-16", upi=1800.00, payout=900.00, net=900.00)

        db.commit()
        print("seed_demo.py: done. See the reference table for merchant IDs, phones, and demo questions.")
    finally:
        db.close()

# =========================================================================
# HELPER FUNCTIONS FOR DIRECT DB INSERTS (BYPASSING REPOS FOR FIXED IDS)
# =========================================================================

def _merchant(db, merchant_id, shop_name, owner_name, phone, cognee_dataset):
    m = Merchant(merchant_id=merchant_id, shop_name=shop_name, owner_name=owner_name, phone=phone, cognee_dataset=cognee_dataset)
    db.add(m)

def _customer(db, customer_id, merchant_id, display_name, canonical_key, phone):
    c = Customer(customer_id=customer_id, merchant_id=merchant_id, display_name=display_name, canonical_key=canonical_key)
    db.add(c)

def _distributor(db, distributor_id, merchant_id, name, canonical_key, upi_id):
    d = Distributor(distributor_id=distributor_id, merchant_id=merchant_id, name=name, canonical_key=canonical_key)
    db.add(d)

def _txn(db, merchant_id, customer_id, amount, txn_type, items, txn_date):
    txn_id = f"txn_{uuid.uuid4().hex[:8]}"
    t = LedgerTransaction(
        txn_id=txn_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        amount=Decimal(str(amount)),
        txn_type=txn_type.value,
        source=TxnSource.MANUAL.value,
        items=items,
        created_at=datetime.fromisoformat(txn_date).replace(tzinfo=timezone.utc)
    )
    db.add(t)
    
    evt = OutboxEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        event_type=EventType.CREDIT_ADDED.value,
        payload={"customer_id": customer_id, "amount": float(amount), "txn_id": txn_id}
    )
    db.add(evt)

def _invoice(db, merchant_id, distributor_id, invoice_date, line_items):
    invoice_id = f"inv_{uuid.uuid4().hex[:8]}"
    total = sum(qty * rate for _, qty, rate in line_items)
    inv = Invoice(
        invoice_id=invoice_id,
        merchant_id=merchant_id,
        distributor_id=distributor_id,
        invoice_date=date.fromisoformat(invoice_date),
        total_amount=Decimal(str(total)),
        is_paid=True
    )
    db.add(inv)
    
    for sku, qty, rate in line_items:
        li = InvoiceLineItem(
            line_item_id=f"li_{uuid.uuid4().hex[:8]}",
            invoice_id=invoice_id,
            distributor_id=distributor_id,
            sku=sku,
            quantity=qty,
            unit="pcs",
            unit_price=Decimal(str(rate))
        )
        db.add(li)
        
    evt = OutboxEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        event_type=EventType.INVOICE_CREATED.value,
        payload={"invoice_id": invoice_id, "distributor_id": distributor_id, "total_amount": float(total)}
    )
    db.add(evt)

def _settlement(db, merchant_id, rollup_date_str, upi, payout, net):
    rollup = SettlementDailyRollup(
        rollup_id=f"roll_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        rollup_date=date.fromisoformat(rollup_date_str),
        upi_collection_total=Decimal(str(upi)),
        payout_total=Decimal(str(payout)),
        net_balance=Decimal(str(net))
    )
    db.add(rollup)

if __name__ == "__main__":
    seed()
