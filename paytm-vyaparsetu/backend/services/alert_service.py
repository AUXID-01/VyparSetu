from sqlalchemy.orm import Session
from db.models import Alert, Merchant
from core.errors import AppException, ErrorCode
from core.logging import get_logger

logger = get_logger("services.alert_service")

def format_alert_dispatch_payload(db: Session, alert_id: str) -> dict:
    # 1. Fetch Alert
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise AppException(
            code="ALERT_NOT_FOUND",
            message=f"Alert {alert_id} not found",
            status_code=404
        )
        
    # 2. Fetch Merchant
    merchant = db.query(Merchant).filter(Merchant.merchant_id == alert.merchant_id).first()
    if not merchant:
        raise AppException(
            code=ErrorCode.MERCHANT_NOT_FOUND,
            message=f"Merchant {alert.merchant_id} not found",
            status_code=404
        )
        
    # 3. Format message
    details = alert.details or {}
    
    if alert.alert_type == "RATE_SPIKE":
        sku = details.get("sku", "Unknown")
        delta = details.get("delta", 0)
        fallback_msg = f"SKU '{sku}' price increased by {delta}"
        formatted_message = f"⚠️ [मूल्य वृद्धि चेतावनी] {merchant.shop_name}: सप्लायर ने दर बढ़ा दी है! {fallback_msg}"
        priority = "MEDIUM"
        
    elif alert.alert_type == "PAYOUT_FAILED":
        reason = details.get("failure_reason", "Unknown error")
        formatted_message = f"🚨 [भुगतान विफल] {merchant.shop_name}: वेंडर को भुगतान नहीं हो सका। कारण: {reason}"
        priority = "HIGH"
        
    elif alert.alert_type == "CREDIT_LIMIT_EXCEEDED":
        fallback_msg = details.get("message", "")
        formatted_message = f"⚠️ [उधार सीमा चेतावनी] {merchant.shop_name}: ग्राहक की बकाया राशि सीमा पार कर गई है। {fallback_msg}"
        priority = "MEDIUM"
        
    else:
        formatted_message = f"ℹ️ [सूचना] {merchant.shop_name}: नया अलर्ट। {details.get('message', '')}"
        priority = "LOW"
        
    payload = {
        "alert_id": alert.alert_id,
        "merchant_id": alert.merchant_id,
        "merchant_phone": merchant.phone,
        "shop_name": merchant.shop_name,
        "alert_type": alert.alert_type,
        "priority": priority,
        "message": formatted_message.strip(),
        "metadata": details
    }
    
    logger.info(f"🔔 [Alert] Formatted dispatch payload for {alert_id} ({alert.alert_type})")
    return payload
