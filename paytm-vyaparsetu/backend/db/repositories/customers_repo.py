from sqlalchemy.orm import Session
from db.models import Customer
from core.ids import generate_customer_id

def get_or_create(db: Session, merchant_id: str, name: str = None, display_name: str = None) -> Customer:
    raw_name = (display_name or name or "").strip()
    clean_canonical = raw_name.lower()
    clean_display = raw_name.capitalize()
    
    # Find existing customer
    existing = db.query(Customer).filter(
        Customer.merchant_id == merchant_id,
        Customer.canonical_key == clean_canonical
    ).first()
    
    if existing:
        return existing
        
    # Create new if doesn't exist
    new_customer = Customer(
        customer_id=generate_customer_id(),
        merchant_id=merchant_id,
        display_name=clean_display,
        canonical_key=clean_canonical
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

def get_customer(db: Session, merchant_id: str, customer_id: str) -> Customer | None:
    return db.query(Customer).filter(
        Customer.merchant_id == merchant_id,
        Customer.customer_id == customer_id
    ).first()

resolve_or_create = get_or_create
