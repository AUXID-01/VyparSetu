from db.session import SessionLocal
from db.models import LedgerTransaction

def check_rows():
    db = SessionLocal()
    mer_gupta = "mer_gupta01"
    count = db.query(LedgerTransaction).filter_by(merchant_id=mer_gupta).count()
    print(f"REAL DB COUNT FOR {mer_gupta}: {count}")
    db.close()

if __name__ == "__main__":
    check_rows()
