from sqlalchemy.orm import Session
from db.models import Customer
from core.ids import generate_customer_id

def get_or_create(db: Session, merchant_id: str, name: str) -> Customer:
    # Canonical logic: lowercase, strip whitespace
    canonical_key = name.strip().lower()
    
    # Find existing customer
    existing = db.query(Customer).filter(
        Customer.merchant_id == merchant_id,
        Customer.canonical_key == canonical_key
    ).first()
    
    if existing:
        return existing
        
    # Create new if doesn't exist
    new_customer = Customer(
        customer_id=generate_customer_id(),
        merchant_id=merchant_id,
        display_name=name.strip(),
        canonical_key=canonical_key
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
