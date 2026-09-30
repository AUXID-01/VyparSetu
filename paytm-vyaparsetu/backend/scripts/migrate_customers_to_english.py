import sys
import os
import json
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from db.session import SessionLocal
from db.models import Customer
from config import settings
from groq import Groq

def is_ascii(s: str) -> bool:
    if not s:
        return True
    return all(ord(c) < 128 for c in s)

FALLBACK_MAP = {
    "आयुष": "Ayush",
    "नंदिनी": "Nandini",
    "रियाद": "Riyadh",
    "स्टूडेंट्स": "Students",
    "कमल": "Kamal",
    "आकाश": "Akash",
    "सुरेश": "Suresh",
    "रमेश": "Ramesh",
    "अमित": "Amit"
}

def transliterate_with_groq(client: Groq, text: str) -> str:
    prompt = f"""Transliterate the following Indian person name or word phonetically into standard English Latin script.
CRITICAL RULE: Do NOT translate to English dictionary words (e.g. 'कमल' -> 'Kamal', NOT 'Lotus'; 'आकाश' -> 'Akash', NOT 'Sky').
Return a JSON object with key 'transliterated_name'.

Word: "{text}" """
    try:
        res = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = res.choices[0].message.content
        data = json.loads(content)
        name = data.get("transliterated_name", "").strip()
        if name:
            return name
        return FALLBACK_MAP.get(text.strip(), text.strip())
    except Exception as exc:
        print(f"  [Groq Fallback Warning] {exc}")
        return FALLBACK_MAP.get(text.strip(), text.strip())

def run_migration():
    print("=" * 60)
    print("🚀 Starting Customer English Normalization Migration")
    print("=" * 60)

    db = SessionLocal()
    groq_client = None
    if settings.GROQ_API_KEY:
        try:
            groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to init Groq client: {e}")

    try:
        customers = db.query(Customer).all()
        print(f"Found {len(customers)} total customers in database.\n")

        updated_count = 0
        for cust in customers:
            old_display = cust.display_name or ""
            old_canonical = cust.canonical_key or ""

            # Check if name contains non-ASCII characters
            needs_migration = not is_ascii(old_display) or not is_ascii(old_canonical)
            
            if needs_migration:
                # Transliterate
                if groq_client:
                    transliterated = transliterate_with_groq(groq_client, old_display)
                else:
                    transliterated = FALLBACK_MAP.get(old_display.strip(), old_display.strip())

                new_display = transliterated.strip().capitalize()
                new_canonical = transliterated.strip().lower()

                # Ensure uniqueness for (merchant_id, canonical_key)
                existing = db.query(Customer).filter(
                    Customer.merchant_id == cust.merchant_id,
                    Customer.canonical_key == new_canonical,
                    Customer.customer_id != cust.customer_id
                ).first()

                if existing:
                    new_canonical = f"{new_canonical}_{cust.customer_id[-4:]}"

                cust.display_name = new_display
                cust.canonical_key = new_canonical
                updated_count += 1

                print(f"  [UPDATED] Customer ID: {cust.customer_id}")
                print(f"    Merchant:      {cust.merchant_id}")
                print(f"    Display Name:  '{old_display}' -> '{new_display}'")
                print(f"    Canonical Key: '{old_canonical}' -> '{new_canonical}'\n")

        if updated_count > 0:
            db.commit()
            print(f"✅ Successfully committed {updated_count} customer updates to PostgreSQL.")
        else:
            print("✨ All customer records are already normalized in English Latin script.")

        print("\n" + "=" * 60)
        print("📊 CURRENT CUSTOMER RECORDS IN POSTGRESQL:")
        print("=" * 60)
        current_rows = db.query(Customer).all()
        for c in current_rows:
            is_clean = is_ascii(c.display_name) and is_ascii(c.canonical_key)
            status = "✅ ASCII CLEAN" if is_clean else "❌ NON-ASCII"
            print(f"• ID: {c.customer_id} | Merchant: {c.merchant_id} | Display: '{c.display_name}' | Canonical: '{c.canonical_key}' | {status}")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
