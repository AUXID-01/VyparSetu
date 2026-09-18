"""
memory/dataset_manager.py
Manages the dataset lifecycle and tenant resolution for Cognee Cloud.
"""

from sqlalchemy.orm import Session
from db.models import Merchant
from core.logging import get_logger

logger = get_logger("memory.dataset_manager")

def get_dataset_for_merchant(db: Session, merchant_id: str) -> str:
    """
    Resolves the canonical dataset name for a given merchant.
    If it doesn't exist on the merchant model, provisions it.
    """
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if not merchant:
        # Fallback for isolation, even if merchant not found locally
        logger.warning(f"Merchant {merchant_id} not found in DB. Returning default dataset.")
        return f"merchant_{merchant_id}"
        
    dataset_name = merchant.cognee_dataset
    if not dataset_name:
        dataset_name = f"merchant_{merchant_id}"
        merchant.cognee_dataset = dataset_name
        db.commit()
        logger.info(f"Provisioned new dataset name '{dataset_name}' for merchant {merchant_id}")
        
    return dataset_name
