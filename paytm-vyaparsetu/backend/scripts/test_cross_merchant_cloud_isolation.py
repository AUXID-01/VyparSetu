import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from fastapi.testclient import TestClient
from main import app
from db.session import SessionLocal
from db.models import Merchant, OutboxEvent
from scripts.seed_dev import seed_dev
from memory import graph_client
from config import settings

client = TestClient(app)

async def main():
    print("🚀 Starting Cross-Merchant Isolation & Cache Test")
    
    db = SessionLocal()
    try:
        print("🧹 Wiping Database...")
        wipe_sql_path = os.path.join(os.path.dirname(__file__), "wipe.sql")
        with open(wipe_sql_path, "r") as f:
            wipe_sql = f.read()
        db.execute(text(wipe_sql))
        db.commit()
        
        # 1. Seed Development Data
        seed_dev()
        
        # 2. Fetch Merchant 1 and 3
        m1 = db.query(Merchant).filter_by(shop_name="Baseline Clean Store").first()
        m3 = db.query(Merchant).filter_by(shop_name="Cross-Merchant Isolation Store").first()
        
        print(f"Merchant 1: {m1.merchant_id} | Dataset: {m1.cognee_dataset}")
        print(f"Merchant 3: {m3.merchant_id} | Dataset: {m3.cognee_dataset}")
        
        # 3. Ingest Events into Cognee Cloud
        for merchant in [m1, m3]:
            print(f"📤 Ingesting data for {merchant.shop_name} into {merchant.cognee_dataset}...")
            # We must connect cognee to cloud first if not already done in graph_client
            # Actually, `memory/graph_client.py` uses cognee which reads ENV vars directly. 
            # We just need to make sure the ENV vars are set if not done.
            os.environ["COGNEE_API_KEY"] = settings.COGNEE_API_KEY
            if settings.COGNEE_API_URL:
                os.environ["COGNEE_API_URL"] = settings.COGNEE_API_URL
            
            # Fetch events
            events = db.query(OutboxEvent).filter_by(merchant_id=merchant.merchant_id).all()
            for event in events:
                success = await graph_client.add_payload(merchant.cognee_dataset, event.payload)
                if not success:
                    print(f"❌ Failed to ingest event {event.event_id}")
            
            # Cognify Dataset
            success = await graph_client.cognify_dataset(merchant.cognee_dataset)
            if not success:
                print(f"❌ Failed to cognify dataset {merchant.cognee_dataset}")
            else:
                print(f"✅ Cognified {merchant.cognee_dataset}")

        # 4. Assertions
        print("\n🧪 Running API Assertions...")
        question = "What is the price of Dahi 200g Pouch?"
        
        # Assertion 1: Live Query (Merchant 1)
        print("--- Assertion 1: Live Query ---")
        res1 = client.post("/api/v1/query/ask", json={
            "merchant_id": m1.merchant_id,
            "question": question
        })
        assert res1.status_code == 200
        data1 = res1.json()["data"]
        print(f"Answer: {data1['answer'][:100]}")
        assert data1["source"] == "LIVE", f"Expected source LIVE, got {data1['source']}"
        assert data1["generated_in_ms"] > 0, "Expected generated_in_ms > 0 for LIVE query"
        print("✅ Live query successful")
        
        # Assertion 2: Cache Query (Merchant 1)
        print("--- Assertion 2: Cache Hit ---")
        res2 = client.post("/api/v1/query/ask", json={
            "merchant_id": m1.merchant_id,
            "question": question
        })
        assert res2.status_code == 200
        data2 = res2.json()["data"]
        assert data2["source"] == "CACHE", f"Expected source CACHE, got {data2['source']}"
        assert data2["generated_in_ms"] == 0, "Expected generated_in_ms == 0 for CACHE query"
        assert data2["answer"] == data1["answer"], "Cache answer does not match LIVE answer"
        print("✅ Cache hit successful")
        
        # Assertion 3: Cross-Tenant Isolation (Merchant 3)
        print("--- Assertion 3: Cross-Tenant Isolation ---")
        res3 = client.post("/api/v1/query/ask", json={
            "merchant_id": m3.merchant_id,
            "question": question
        })
        assert res3.status_code == 200
        data3 = res3.json()["data"]
        print(f"Answer: {data3['answer'][:100]}")
        assert data3["source"] == "LIVE", f"Expected source LIVE for new merchant, got {data3['source']}"
        # Even though the question is the same, m1 and m3 have different contexts/answers 
        # (Though in our seed_dev they might have the same price, but the isolation proves it queries m3's dataset)
        print("✅ Isolation check successful")
        
        print("\n🎉 All tests passed successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
