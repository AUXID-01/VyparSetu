import sys
import os
from unittest.mock import patch

# Reconfigure stdout for UTF-8 compatibility on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from db.session import SessionLocal
from db.models import Merchant, LedgerTransaction, OutboxEvent
from db.repositories import merchants_repo

client = TestClient(app)

def test_voice_e2e():
    db = SessionLocal()
    try:
        # Step 1: Ensure test merchant exists
        merchant_id = "mer_test_01"
        merchant = db.query(Merchant).filter_by(merchant_id=merchant_id).first()
        if not merchant:
            merchant = Merchant(
                merchant_id=merchant_id,
                shop_name="E2E Test Store",
                owner_name="Test Merchant",
                phone="+919000011122",
                cognee_dataset=f"merchant_{merchant_id}"
            )
            db.add(merchant)
            db.commit()
            print(f"[1/4] Created test merchant: {merchant_id}")
        else:
            print(f"[1/4] Using existing merchant: {merchant_id}")

        # Step 2: Test Empty Audio Clip Guard (LOW_CONFIDENCE_EXTRACTION)
        print("[2/4] Testing empty audio clip error response...")
        resp_empty = client.post(
            "/api/v1/voice/log-credit-from-audio",
            data={"merchant_id": merchant_id},
            files={"audio": ("empty.wav", b"short", "audio/wav")}
        )
        assert resp_empty.status_code == 400
        res_empty_json = resp_empty.json()
        assert res_empty_json["success"] is False
        assert res_empty_json["error"]["code"] == "LOW_CONFIDENCE_EXTRACTION"
        print("  -> Passed! Empty audio clip correctly returned 400 LOW_CONFIDENCE_EXTRACTION")

        # Step 3: Test Full Voice Credit Fast-Path (Mocking Sarvam STT/TTS for network-independent test)
        print("[3/4] Testing full voice credit pipeline...")
        fake_audio_bytes = b"0" * 2000  # Valid >1000 byte dummy audio payload

        with patch("sarvam.transcribe_audio") as mock_stt, \
             patch("sarvam.synthesize_speech") as mock_tts:
            
            mock_stt.return_value = {
                "transcript": "suresh ji 240 rupaye ka dahi",
                "language_code": "hi-IN"
            }
            mock_tts.return_value = b"fake_b64_audio_bytes"

            resp_full = client.post(
                "/api/v1/voice/log-credit-from-audio",
                data={"merchant_id": merchant_id},
                files={"audio": ("suresh_credit.wav", fake_audio_bytes, "audio/wav")}
            )
            
            assert resp_full.status_code == 200
            res_json = resp_full.json()
            assert res_json["success"] is True
            data = res_json["data"]
            
            assert data["txn_id"].startswith("txn_")
            assert data["customer_id"].startswith("cus_")
            assert data["new_balance"] >= 240.0
            assert "suresh ji ke khate mein" in data["confirmation_audio_text"].lower()
            assert len(data["confirmation_audio_b64"]) > 0
            print(f"  -> Passed! Txn ID: {data['txn_id']}, Balance: ₹{data['new_balance']}")

        # Step 4: Verify Database Invariants (Ledger + Pending Outbox Event)
        print("[4/4] Verifying database invariants in PostgreSQL...")
        txn_id = data["txn_id"]
        txn_row = db.query(LedgerTransaction).filter_by(txn_id=txn_id).first()
        assert txn_row is not None
        assert float(txn_row.amount) == 240.0
        assert txn_row.source == "VOICE"

        outbox_row = db.query(OutboxEvent).filter_by(
            merchant_id=merchant_id,
            event_type="CREDIT_ADDED"
        ).order_by(OutboxEvent.created_at.desc()).first()
        assert outbox_row is not None
        assert outbox_row.status == "PENDING"
        assert outbox_row.payload["txn_id"] == txn_id
        print("  -> Passed! Postgres ledger row & PENDING outbox event verified!")

        print("\nALL Voice E2E Pipeline Checks Passed Successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    test_voice_e2e()
