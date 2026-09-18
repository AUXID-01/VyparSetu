from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
from config import settings
from pydantic import BaseModel
from api.deps import get_db
from db.repositories import merchants_repo
from core.errors import AppException, ErrorCode, success_envelope

router = APIRouter()

class MerchantCreateReq(BaseModel):
    shop_name: str
    owner_name: str
    phone: str
    password: str

class MerchantLoginReq(BaseModel):
    phone: str
    password: str
@router.post("")
def create_merchant(req: MerchantCreateReq, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing = merchants_repo.get_merchant_by_phone(db, req.phone)
    if existing:
        raise AppException(
            code=ErrorCode.DUPLICATE_MERCHANT_PHONE,
            message="A merchant with this phone number already exists.",
            status_code=409
        )
    
    merchant = merchants_repo.create_merchant(
        db=db,
        shop_name=req.shop_name,
        owner_name=req.owner_name,
        phone=req.phone
    )
    
    def trigger_n8n_onboarding(merchant_id: str, shop_name: str, phone: str):
        from core.logging import get_logger
        logger = get_logger("routes.merchants")
        try:
            url = getattr(settings, "N8N_ONBOARDING_WEBHOOK_URL", "http://localhost:5678/webhook/merchant-onboarding")
            payload = {"merchant_id": merchant_id, "shop_name": shop_name, "phone": phone}
            logger.info(f"📤 [Onboarding] Dispatching to n8n webhook -> {payload}")
            httpx.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logger.warning(f"⚠️ [Onboarding] n8n Webhook unreachable, merchant registration succeeds anyway. {e}")

    background_tasks.add_task(trigger_n8n_onboarding, merchant.merchant_id, merchant.shop_name, merchant.phone)
    return success_envelope({
        "merchant_id": merchant.merchant_id,
        "shop_name": merchant.shop_name,
        "owner_name": merchant.owner_name,
        "phone": merchant.phone,
        "cognee_dataset": merchant.cognee_dataset,
        "session_token": f"mock_tok_{merchant.merchant_id}"
    })

@router.get("/{merchant_id}")
def get_merchant(merchant_id: str, db: Session = Depends(get_db)):
    merchant = merchants_repo.get_merchant_by_id(db, merchant_id)
    if not merchant:
        raise AppException(
            code=ErrorCode.MERCHANT_NOT_FOUND,
            message="Merchant not found",
            status_code=404
        )
    return success_envelope({
        "merchant_id": merchant.merchant_id,
        "shop_name": merchant.shop_name,
        "owner_name": merchant.owner_name,
        "phone": merchant.phone,
        "cognee_dataset": merchant.cognee_dataset
    })

@router.post("/login")
def login_merchant(req: MerchantLoginReq, db: Session = Depends(get_db)):
    merchant = merchants_repo.get_merchant_by_phone(db, req.phone)
    if not merchant:
        raise AppException(
            code=ErrorCode.MERCHANT_NOT_FOUND,
            message="Merchant not found",
            status_code=404
        )
    # Simple mock check for hackathon: any password passes if merchant exists
    # In a real app we would check hashed passwords here
    return success_envelope({
        "merchant_id": merchant.merchant_id,
        "shop_name": merchant.shop_name,
        "owner_name": merchant.owner_name,
        "phone": merchant.phone,
        "cognee_dataset": merchant.cognee_dataset,
        "session_token": f"mock_tok_{merchant.merchant_id}"
    })
