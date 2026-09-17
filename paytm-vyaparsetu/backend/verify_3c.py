import httpx
import json
import random

base_url = "http://localhost:8000/api/v1"

# 1. Create merchant
print("Creating merchant...")
rand_suffix = str(random.randint(1000, 9999))
r1 = httpx.post(f"{base_url}/merchants", json={
    "shop_name": "Test Store",
    "owner_name": "Ramesh",
    "phone": f"+9190000{rand_suffix}"
})
print(r1.status_code, r1.text)
merchant_id = r1.json()["data"]["merchant_id"]

# 2. Log Suresh 240
print("\nLogging Suresh 240...")
r2 = httpx.post(f"{base_url}/voice/log-credit", json={
    "merchant_id": merchant_id,
    "raw_transcript": "fake",
    "extracted": {
        "customer_name": "Suresh",
        "amount": 240.00,
        "items": ["Dahi"],
        "confidence": 0.91
    }
})
print(r2.status_code, r2.text)
customer_id = r2.json()["data"]["customer_id"]

# 3. Log suresh 60
print("\nLogging suresh 60...")
r3 = httpx.post(f"{base_url}/voice/log-credit", json={
    "merchant_id": merchant_id,
    "raw_transcript": "fake",
    "extracted": {
        "customer_name": "suresh",
        "amount": 60.00,
        "items": ["Bread"],
        "confidence": 0.91
    }
})
print(r3.status_code, r3.text)

# 4. Query Dues
print("\nQuerying dues...")
r4 = httpx.get(f"{base_url}/query/customer-due/{customer_id}")
print(r4.status_code, r4.text)

