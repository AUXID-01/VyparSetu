"""
scripts/verify_native_workers.py
Runtime verification script for Native Worker Architecture & n8n Decommissioning.

Verifies:
  1. Worker Session Safety: Pool check-in/out, automatic commit, exception rollback, zero handle leaks.
  2. Local Native Settlement: Settle vendor invoice, UTR generation, balance & ceiling validation, DB persistence.
  3. Persistent Outbox Worker Loop: Event processing (PENDING -> SYNCED), stuck event recovery (>5m), graceful loop shutdown.
"""

import sys
import os
import asyncio
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.session import engine, SessionLocal
from db.models import Merchant, Customer, Invoice, Alert, OutboxEvent, Distributor
from workers.context import get_worker_db
from workers.payout_worker import settle_vendor_invoice
from workers.outbox_worker import process_pending_outbox_batch, run_outbox_loop
from core.ids import generate_merchant_id, generate_id

def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_session_safety():
    print_banner("1. Testing Worker Session Safety & Isolation")
    
    # Check pool status before
    initial_checkedout = engine.pool.checkedout()
    print(f"[*] Initial connection pool checkedout handles: {initial_checkedout}")
    
    # 1. Test clean commit
    test_merchant_id = generate_merchant_id()
    phone_clean = f"+9199{test_merchant_id[-8:]}"
    print(f"[*] Testing automatic commit inside get_worker_db()...")
    with get_worker_db() as db:
        m = Merchant(
            merchant_id=test_merchant_id,
            shop_name="Worker Session Test Shop",
            owner_name="Session Tester",
            phone=phone_clean
        )
        db.add(m)
        
    # Verify outside context manager using a fresh session
    with SessionLocal() as verify_db:
        found = verify_db.query(Merchant).filter(Merchant.merchant_id == test_merchant_id).first()
        assert found is not None, "FAILED: Record was not automatically committed by get_worker_db()!"
        print(f"  -> Successfully verified auto-commit: merchant '{found.merchant_id}' exists in DB.")
        
    # 2. Test rollback on exception
    phone_fail = f"+9198{test_merchant_id[-8:]}"
    failed_id = generate_merchant_id()
    print(f"[*] Testing exception rollback in get_worker_db()...")
    try:
        with get_worker_db() as db:
            m_fail = Merchant(
                merchant_id=failed_id,
                shop_name="Should Rollback Shop",
                owner_name="Rollback Tester",
                phone=phone_fail
            )
            db.add(m_fail)
            raise RuntimeError("Simulated worker error triggering rollback")
    except RuntimeError:
        pass
        
    with SessionLocal() as verify_db:
        should_be_none = verify_db.query(Merchant).filter(Merchant.merchant_id == failed_id).first()
        assert should_be_none is None, "FAILED: Uncommitted transaction leaked through exception!"
        print(f"  -> Successfully verified rollback: merchant '{failed_id}' was NOT saved to DB.")
        
    # 3. Test handle leak after multiple operations
    for i in range(10):
        with get_worker_db() as db:
            db.query(Merchant).count()
            
    final_checkedout = engine.pool.checkedout()
    print(f"[*] Final connection pool checkedout handles: {final_checkedout}")
    assert final_checkedout == 0, f"FAILED: Connection pool handle leak detected! Checked out: {final_checkedout}"
    print("✅ [PASS] Worker DB session isolation verified: zero connection pool leaks.")
    return test_merchant_id


def test_local_settlement(merchant_id: str):
    print_banner("2. Testing Local Native Settlement (payout_worker)")
    
    with SessionLocal() as db:
        # Create a test distributor
        dist_id = generate_id("dis_")
        dist = Distributor(
            distributor_id=dist_id,
            merchant_id=merchant_id,
            name="Test Dairy Supply",
            canonical_key="test_dairy_supply"
        )
        db.add(dist)
        
        # Create a normal test invoice (<= 10000)
        inv_id = generate_id("inv_test_")
        inv = Invoice(
            invoice_id=inv_id,
            merchant_id=merchant_id,
            distributor_id=dist_id,
            invoice_date=date.today(),
            total_amount=Decimal("850.00"),
            is_paid=False
        )
        db.add(inv)
        
        # Create an over-ceiling invoice (> 10000)
        inv_large_id = generate_id("inv_large_")
        inv_large = Invoice(
            invoice_id=inv_large_id,
            merchant_id=merchant_id,
            distributor_id=dist_id,
            invoice_date=date.today(),
            total_amount=Decimal("15000.00"),
            is_paid=False
        )
        db.add(inv_large)
        db.commit()

    print(f"[*] Test Invoices seeded: normal='{inv_id}' (Rs. 850.00), over-ceiling='{inv_large_id}' (Rs. 15,000.00)")
    
    # 1. Settle normal invoice
    print(f"[*] Invoking settle_vendor_invoice for normal invoice '{inv_id}'...")
    res = settle_vendor_invoice(invoice_id=inv_id, merchant_id=merchant_id)
    print(f"  -> Settle response: {res}")
    assert res["payout_status"] == "SUCCEEDED", f"Settlement failed: {res}"
    assert res["payout_reference"].startswith("PAYTM_UTR_"), f"Invalid UTR: {res['payout_reference']}"
    
    # Verify in DB
    with SessionLocal() as db:
        inv_db = db.query(Invoice).filter(Invoice.invoice_id == inv_id).first()
        assert inv_db.is_paid == True, "Invoice is_paid was not set to True in DB!"
        assert inv_db.payout_reference == res["payout_reference"], "Invoice payout_reference does not match UTR!"
        assert inv_db.paid_at is not None, "Invoice paid_at timestamp was not set!"
        print(f"  -> DB Verification: is_paid={inv_db.is_paid}, UTR={inv_db.payout_reference}, paid_at={inv_db.paid_at}")
        
        # Verify Outbox record
        outbox = db.query(OutboxEvent).filter(
            OutboxEvent.merchant_id == merchant_id,
            OutboxEvent.event_type == "PAYOUT_SETTLED"
        ).first()
        assert outbox is not None, "Outbox event for PAYOUT_SETTLED was not created!"
        assert outbox.status == "SYNCED", f"Outbox status expected SYNCED, got {outbox.status}"
        print(f"  -> DB Verification: Outbox event '{outbox.event_id}' created with status={outbox.status}")
        
    # 2. Test Ceiling Limit Guard (> 10000)
    print(f"[*] Invoking settle_vendor_invoice for over-ceiling invoice '{inv_large_id}'...")
    res_large = settle_vendor_invoice(invoice_id=inv_large_id, merchant_id=merchant_id)
    print(f"  -> Over-ceiling response: {res_large}")
    assert res_large["payout_status"] == "FAILED", "Large payout should have been rejected!"
    assert "exceeded" in res_large.get("failure_reason", "").lower()
    
    with SessionLocal() as db:
        inv_large_db = db.query(Invoice).filter(Invoice.invoice_id == inv_large_id).first()
        assert inv_large_db.is_paid == False, "Large invoice should remain unpaid!"
        
        alert = db.query(Alert).filter(
            Alert.merchant_id == merchant_id,
            Alert.alert_type == "PAYOUT_FAILED"
        ).first()
        assert alert is not None, "Alert was not recorded for rejected payout ceiling!"
        print(f"  -> DB Verification: Alert '{alert.alert_id}' logged: {alert.details}")
        
    print("✅ [PASS] Local settlement worker verified: payments committed, ceiling enforced, alerts recorded.")


async def test_outbox_loop(merchant_id: str):
    print_banner("3. Testing Persistent Outbox Loop & Recovery (outbox_worker)")
    
    # 1. Ensure test customer exists for merchant
    test_cus_id = f"cus_{merchant_id[-6:]}"
    with SessionLocal() as db:
        cust = db.query(Customer).filter(Customer.customer_id == test_cus_id).first()
        if not cust:
            cust = Customer(
                customer_id=test_cus_id,
                merchant_id=merchant_id,
                display_name="Test Customer",
                canonical_key="test_customer",
                phone="+919800000099"
            )
            db.add(cust)
            db.commit()

    # 2. Insert a PENDING outbox event
    pending_event_id = generate_id("out_pend_")
    with SessionLocal() as db:
        evt = OutboxEvent(
            event_id=pending_event_id,
            merchant_id=merchant_id,
            event_type="CREDIT_ADDED",
            payload={"customer_id": test_cus_id, "amount": 120.0},
            status="PENDING",
            created_at=datetime.now(timezone.utc)
        )
        db.add(evt)
        
        # 2. Insert a STUCK event (status=PROCESSING, created > 5 mins ago)
        stuck_event_id = generate_id("out_stuck_")
        stuck_evt = OutboxEvent(
            event_id=stuck_event_id,
            merchant_id=merchant_id,
            event_type="INVOICE_CREATED",
            payload={"invoice_id": "inv_stuck_01", "amount": 500.0},
            status="PROCESSING",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )
        db.add(stuck_evt)
        db.commit()
        
    print(f"[*] Created test outbox events: PENDING='{pending_event_id}', STUCK='{stuck_event_id}' (10m old)")
    
    # 3. Run outbox processing batch
    print("[*] Running process_pending_outbox_batch()...")
    total_processed = 0
    while True:
        count = process_pending_outbox_batch(limit=50)
        total_processed += count
        if count == 0:
            break
    print(f"  -> Batch processing completed. Total events processed: {total_processed}")
    assert total_processed >= 2, f"Expected at least 2 events processed, got {total_processed}"
    
    # 4. Verify in DB
    with SessionLocal() as db:
        evt1 = db.query(OutboxEvent).filter(OutboxEvent.event_id == pending_event_id).first()
        evt2 = db.query(OutboxEvent).filter(OutboxEvent.event_id == stuck_event_id).first()
        
        assert evt1.status == "SYNCED", f"Pending event status is {evt1.status}, expected SYNCED"
        assert evt1.synced_at is not None, "Pending event synced_at timestamp was not set"
        print(f"  -> Event '{evt1.event_id}': status={evt1.status}, synced_at={evt1.synced_at}")
        
        assert evt2.status == "SYNCED", f"Stuck event status is {evt2.status}, expected SYNCED (after recovery)"
        assert evt2.synced_at is not None, "Stuck event synced_at timestamp was not set"
        print(f"  -> Event '{evt2.event_id}': status={evt2.status}, recovered and synced_at={evt2.synced_at}")
        
    # 5. Test asynchronous lifespan run_outbox_loop with stop_event
    print("[*] Testing run_outbox_loop graceful start & shutdown via asyncio.Event()...")
    stop_event = asyncio.Event()
    loop_task = asyncio.create_task(run_outbox_loop(stop_event, interval_seconds=1))
    
    # Allow loop to start and run a pass
    await asyncio.sleep(0.5)
    assert not loop_task.done(), "Loop terminated prematurely!"
    
    # Signal shutdown
    stop_event.set()
    await asyncio.wait_for(loop_task, timeout=2.0)
    assert loop_task.done(), "Loop did not stop gracefully when stop_event was set!"
    print("  -> Outbox worker loop stopped cleanly upon stop_event signal.")
    
    print("✅ [PASS] Persistent outbox worker verified: processing, recovery, and graceful shutdown.")


def main():
    print("\n" + "#" * 70)
    print("  RUNNING NATIVE WORKER ARCHITECTURE RUNTIME VERIFICATION")
    print("#" * 70)
    
    # Step 1: Session safety
    merchant_id = test_session_safety()
    
    # Step 2: Local settlement
    test_local_settlement(merchant_id)
    
    # Step 3: Outbox loop
    asyncio.run(test_outbox_loop(merchant_id))
    
    print("\n" + "=" * 70)
    print("🎉 ALL NATIVE WORKER & N8N DECOMMISSION VERIFICATION CHECKS PASSED!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
