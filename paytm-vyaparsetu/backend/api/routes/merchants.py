from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.deps import get_db
from db.repositories import merchants_repo
from core.errors import AppException, ErrorCode, success_envelope

router = APIRouter()

class MerchantCreateReq(BaseModel):
    shop_name: str
    owner_name: str
    phone: str

@router.post("")
def create_merchant(req: MerchantCreateReq, db: Session = Depends(get_db)):
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
    
    # TODO: wire n8n onboarding webhook in Phase 8
    
    return success_envelope({
        "merchant_id": merchant.merchant_id,
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
