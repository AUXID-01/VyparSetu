"""
scripts/reset_db.py
CLI wrapper to execute wipe.sql against the database session to safely truncate all tables.
Run with: python -m scripts.reset_db
"""

import os
from sqlalchemy import text
from api.deps import SessionLocal

def main():
    print("⚠️ WARNING: This will truncate ALL tables in the database.")
    confirmation = input("Are you sure you want to proceed? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Aborting.")
        return

    wipe_sql_path = os.path.join(os.path.dirname(__file__), 'wipe.sql')
    
    with open(wipe_sql_path, 'r') as f:
        sql = f.read()

    db = SessionLocal()
    try:
        print("Executing wipe.sql...")
        db.execute(text(sql))
        db.commit()
        print("✅ Database successfully wiped clean.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error wiping database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
