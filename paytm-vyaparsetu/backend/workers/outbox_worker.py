import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import func
from db.models import OutboxEvent
from core.logging import get_logger
from workers.context import get_worker_db
from workers.notification_worker import send_whatsapp_payment_link

logger = get_logger("workers.outbox_worker")

def process_single_outbox_event(db, event: OutboxEvent) -> bool:
    """
    Processes an individual outbox event based on its event_type.
    Returns True if successfully processed, False if failed.
    """
    event_type = event.event_type
    payload = event.payload or {}
    merchant_id = event.merchant_id
    
    logger.info(f"🔄 [Outbox Worker] Processing event='{event.event_id}', type='{event_type}', merchant='{merchant_id}'")
    
    try:
        if event_type == "CREDIT_ADDED":
            customer_id = payload.get("customer_id")
            amount = float(payload.get("amount", 0.0))
            if customer_id and amount > 0:
                send_whatsapp_payment_link(merchant_id=merchant_id, customer_id=customer_id, amount=amount)
                
        elif event_type == "INVOICE_CREATED":
            invoice_id = payload.get("invoice_id")
            logger.info(f"📄 [Outbox Worker] Inbound invoice event recorded: {invoice_id}")
            
        elif event_type == "PAYOUT_SETTLED":
            invoice_id = payload.get("invoice_id")
            utr = payload.get("utr_reference")
            logger.info(f"💳 [Outbox Worker] Vendor payout event synced: invoice='{invoice_id}', UTR='{utr}'")
            
        elif event_type == "SETTLEMENT_ROLLUP":
            logger.info(f"📊 [Outbox Worker] Daily rollup event processed for merchant='{merchant_id}'")
            
        # Successfully processed
        event.status = "SYNCED"
        event.synced_at = datetime.now(timezone.utc)
        logger.info(f"✅ [Outbox Worker] Marked event='{event.event_id}' as SYNCED")
        return True
        
    except Exception as exc:
        event.attempt_count = (event.attempt_count or 0) + 1
        if event.attempt_count >= 5:
            event.status = "FAILED"
            logger.error(f"❌ [Outbox Worker] Event='{event.event_id}' failed 5 attempts, marked FAILED: {exc}")
        else:
            logger.warning(f"⚠️ [Outbox Worker] Event='{event.event_id}' attempt {event.attempt_count} failed: {exc}")
        return False

def process_pending_outbox_batch(limit: int = 20) -> int:
    """
    Executes a single batch pass over pending or stuck outbox events.
    Recovers stuck events older than 5 minutes and processes pending events.
    Returns the number of events processed.
    """
    processed_count = 0
    with get_worker_db() as db:
        # 1. Recover stuck events older than 5 minutes (e.g. if worker crashed during processing)
        stuck_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        stuck_events = db.query(OutboxEvent).filter(
            OutboxEvent.status == "PROCESSING",
            OutboxEvent.created_at <= stuck_cutoff
        ).all()
        for stuck in stuck_events:
            logger.warning(f"⚠️ [Outbox Worker] Recovering stuck event '{stuck.event_id}' back to PENDING")
            stuck.status = "PENDING"

        # 2. Fetch pending events ordered chronologically
        events = db.query(OutboxEvent).filter(
            OutboxEvent.status == "PENDING"
        ).order_by(OutboxEvent.created_at.asc()).limit(limit).all()
        
        for event in events:
            success = process_single_outbox_event(db, event)
            if success:
                processed_count += 1
                
    return processed_count

async def run_outbox_loop(stop_event: asyncio.Event, interval_seconds: int = 15):
    """
    Persistent async background loop managing the outbox table.
    Polls every interval_seconds until stop_event is signaled during application shutdown.
    """
    logger.info(f"🚀 [Outbox Worker] Starting persistent outbox polling loop (interval={interval_seconds}s)")
    while not stop_event.is_set():
        try:
            # Run batch synchronously within thread pool to avoid blocking the asyncio event loop
            count = await asyncio.to_thread(process_pending_outbox_batch, limit=25)
            if count > 0:
                logger.info(f"📦 [Outbox Worker] Successfully processed {count} pending events in batch")
        except Exception as exc:
            logger.error(f"🚨 [Outbox Worker] Error in outbox processing pass: {exc}", exc_info=True)
            
        try:
            # Wait for either the sleep duration or shutdown signal
            await asyncio.wait_for(stop_event.wait(), timeout=float(interval_seconds))
        except asyncio.TimeoutError:
            pass

    logger.info("🛑 [Outbox Worker] Outbox worker loop stopped cleanly.")
