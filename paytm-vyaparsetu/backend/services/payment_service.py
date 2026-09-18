import uuid
from sqlalchemy.orm import Session
from db.models import Customer, Merchant
from core.errors import AppException, ErrorCode
from core.logging import get_logger

logger = get_logger("services.payment_service")

def generate_payment_link_payload(db: Session, merchant_id: str, customer_id: str, amount: float) -> dict:
    """
    Generates a payment link payload including dynamic Hindi/Hinglish messaging.
    """
    # 1. Fetch Merchant
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if not merchant:
        raise AppException(
            code=ErrorCode.MERCHANT_NOT_FOUND,
            message=f"Merchant {merchant_id} not found",
            status_code=404
        )
        
    # 2. Fetch Customer
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id, 
        Customer.merchant_id == merchant_id
    ).first()
    if not customer:
        raise AppException(
            code=ErrorCode.CUSTOMER_NOT_FOUND,
            message=f"Customer {customer_id} not found for merchant {merchant_id}",
            status_code=404
        )
        
    # 3. Generate Link & Message
    payment_url = f"https://paytm.me/mock-{uuid.uuid4().hex[:8]}"
    message = f"नमस्ते {customer.display_name}, {merchant.shop_name} पर आपका ₹{amount:.2f} का उधार दर्ज हुआ है। विवरण देखें या भुगतान करें: {payment_url}"
    
    payload = {
        "phone": customer.phone,
        "customer_name": customer.display_name,
        "merchant_name": merchant.shop_name,
        "amount": amount,
        "payment_url": payment_url,
        "message": message
    }
    
    logger.info(f"🔗 [Payment Link] Generated payload for customer {customer_id} (Merchant {merchant_id}) - Amount: {amount}")
    return payload
