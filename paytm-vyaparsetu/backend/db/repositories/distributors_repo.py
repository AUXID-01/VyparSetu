from typing import Optional
from sqlalchemy.orm import Session
from db.models import Distributor
from core.ids import generate_id
from core.logging import get_logger

logger = get_logger("db.distributors_repo")

def resolve_or_create(db: Session, merchant_id: str, name: str, upi_id: Optional[str] = None) -> Distributor:
    """
    Resolves an existing distributor by normalized name, or creates a new one.
    Canonical key is name.strip().lower().
    """
    canonical_key = name.strip().lower()
    
    distributor = db.query(Distributor).filter(
        Distributor.merchant_id == merchant_id,
        Distributor.canonical_key == canonical_key
    ).first()
    
    if distributor:
        logger.info(f"🔍 [DB Read] Distributor resolved: {distributor.distributor_id} (name: '{name}')")
        # Update upi_id if provided and current is None? Optional, let's stick to simple resolution
        return distributor
        
    distributor_id = generate_id("dis_")
    distributor = Distributor(
        distributor_id=distributor_id,
        merchant_id=merchant_id,
        name=name.strip(),
        upi_id=upi_id,
        canonical_key=canonical_key
    )
    
    db.add(distributor)
    # We don't commit here, we let the service layer handle the transaction
    logger.info(f"💾 [DB Write] New Distributor created: {distributor_id} (name: '{name}')")
    return distributor
