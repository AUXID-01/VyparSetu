from sqlalchemy.orm import Session
from db.models import Merchant
from core.ids import generate_merchant_id

def create_merchant(db: Session, shop_name: str, owner_name: str, phone: str) -> Merchant:
    merchant = Merchant(
        merchant_id=generate_merchant_id(),
        shop_name=shop_name,
        owner_name=owner_name,
        phone=phone,
        cognee_dataset=f"dataset_{phone}"
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant

def get_merchant_by_id(db: Session, merchant_id: str) -> Merchant | None:
    return db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()

def get_merchant_by_phone(db: Session, phone: str) -> Merchant | None:
    return db.query(Merchant).filter(Merchant.phone == phone).first()
