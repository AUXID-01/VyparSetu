from workers.context import get_worker_db
from services import payment_service, alert_service
from core.logging import get_logger

logger = get_logger("workers.notification_worker")

def send_whatsapp_payment_link(merchant_id: str, customer_id: str, amount: float) -> dict:
    """
    Background worker task to generate and dispatch a simulated WhatsApp payment link.
    Invoked via FastAPI BackgroundTasks when customer credit is logged.
    """
    logger.info(f"📲 [Notification Worker] Dispatching payment link for customer='{customer_id}', merchant='{merchant_id}', amount={amount}")
    try:
        with get_worker_db() as db:
            payload = payment_service.generate_payment_link_payload(db, merchant_id, customer_id, amount)
            
            # Simulated WhatsApp Cloud API / Twilio call
            logger.info(
                f"✅ [WhatsApp Mock Dispatch] To: {payload.get('phone')} | "
                f"Merchant: {payload.get('merchant_name')} | "
                f"Amount: ₹{amount:.2f} | Message: {payload.get('message')}"
            )
            return {"status": "DELIVERED", "channel": "WHATSAPP", "payload": payload}
    except Exception as e:
        logger.error(f"❌ [Notification Worker] Failed to send payment link: {e}", exc_info=True)
        return {"status": "FAILED", "error": str(e)}

def dispatch_rate_spike_alert(merchant_id: str, alert_id: str) -> dict:
    """
    Background worker task to format and dispatch supplier rate hike alerts.
    """
    logger.info(f"🔔 [Notification Worker] Dispatching rate spike alert='{alert_id}', merchant='{merchant_id}'")
    try:
        with get_worker_db() as db:
            payload = alert_service.format_alert_dispatch_payload(db, alert_id)
            
            logger.info(
                f"🚨 [Alert Mock Dispatch] To Merchant Phone: {payload.get('merchant_phone')} | "
                f"Type: {payload.get('alert_type')} | "
                f"Priority: {payload.get('priority')} | Message: {payload.get('message')}"
            )
            return {"status": "DELIVERED", "channel": "WHATSAPP_URGENT", "payload": payload}
    except Exception as e:
        logger.error(f"❌ [Notification Worker] Failed to dispatch alert: {e}", exc_info=True)
        return {"status": "FAILED", "error": str(e)}

def dispatch_merchant_welcome(merchant_id: str, shop_name: str, phone: str) -> dict:
    """
    Background worker task to dispatch onboarding welcome message to newly registered merchants.
    """
    logger.info(f"🎉 [Notification Worker] Dispatching welcome notification for merchant='{merchant_id}' ({shop_name})")
    welcome_text = f"नमस्ते! Paytm VyaparSetu में आपका स्वागत है। {shop_name} के लिए आपका स्मार्ट खाता और AI बहीखाता तैयार है।"
    logger.info(f"✅ [WhatsApp Welcome Dispatch] To: {phone} | Message: {welcome_text}")
    return {"status": "DELIVERED", "merchant_id": merchant_id, "message": welcome_text}
