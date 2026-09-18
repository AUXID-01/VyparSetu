import base64
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from db.repositories import customers_repo, ledger_repo, outbox_repo
from core.enums import TxnType, LedgerSource, OutboxEventType
from core.errors import AppException, ErrorCode
from db.models import LedgerTransaction
import sarvam
import extraction

def process_log_credit(
    db: Session,
    merchant_id: str,
    customer_name: str,
    amount: float,
    items: list[str],
    confidence: float
) -> dict:
    
    # 1. Resolve/create customer
    customer = customers_repo.get_or_create(db, merchant_id, customer_name)
    
    # 2. Insert ledger transaction
    txn = ledger_repo.create_transaction(
        db=db,
        merchant_id=merchant_id,
        customer_id=customer.customer_id,
        amount=amount,
        txn_type=TxnType.CREDIT_ADDED.value,
        source=LedgerSource.VOICE.value,
        items=items,
        extraction_confidence=confidence
    )
    
    # 3. Insert outbox_events row
    outbox_repo.create_event(
        db=db,
        merchant_id=merchant_id,
        event_type=OutboxEventType.CREDIT_ADDED.value,
        payload={
            "txn_id": txn.txn_id,
            "customer_id": customer.customer_id,
            "merchant_id": merchant_id,
            "amount": amount
        }
    )
    
    current_balance = ledger_repo.calculate_customer_due(db, merchant_id, customer.customer_id)
    
    # Confirmation text
    confirmation_text = f"{customer.display_name} ji ke khate mein {amount} rupaye jod diye gaye hain."
    
    return {
        "txn_id": txn.txn_id,
        "customer_id": customer.customer_id,
        "new_balance": float(current_balance),
        "confirmation_audio_text": confirmation_text
    }


def process_voice_credit_audio(
    db: Session,
    merchant_id: str,
    audio_bytes: bytes,
    filename: str = "audio.wav"
) -> dict:
    """
    Full counter-speed voice credit pipeline:
    Audio Upload -> Sarvam STT -> Extraction -> Low Confidence Guard -> Postgres DB -> Number-to-Words -> Sarvam TTS -> Spoken Audio & JSON
    """
    # Step A (Input Guard)
    if len(audio_bytes) < 1000:
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Empty or inaudible voice clip",
            status_code=400
        )

    # Step B (STT)
    stt_res = sarvam.transcribe_audio(audio_bytes=audio_bytes, filename=filename)
    raw_transcript = stt_res.get("transcript", "")
    if not raw_transcript.strip():
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="No clear speech detected",
            status_code=400
        )

    # Step C (Extraction)
    extracted = extraction.extract_entities(raw_transcript)

    # Step D (Confidence Guard)
    confidence = extracted.get("confidence", 0.0)
    customer_name = extracted.get("customer_name")
    amount = float(extracted.get("amount", 0.0))

    if confidence < 0.6 or not customer_name or amount <= 0:
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message=f"Could not reliably extract credit details from: '{raw_transcript}'",
            status_code=400
        )

    # Step E (Database Ledger Invariants)
    customer = customers_repo.resolve_or_create(db, merchant_id=merchant_id, display_name=customer_name)
    
    txn = ledger_repo.create_transaction(
        db=db,
        merchant_id=merchant_id,
        customer_id=customer.customer_id,
        amount=amount,
        txn_type=TxnType.CREDIT_ADDED.value,
        source=LedgerSource.VOICE.value,
        items=extracted.get("items", []),
        extraction_confidence=confidence
    )

    outbox_repo.create_outbox_event(
        db=db,
        merchant_id=merchant_id,
        event_type=OutboxEventType.CREDIT_ADDED.value,
        payload={
            "txn_id": txn.txn_id,
            "customer_id": customer.customer_id,
            "merchant_id": merchant_id,
            "amount": float(txn.amount)
        }
    )

    new_balance = ledger_repo.calculate_customer_due(db, merchant_id=merchant_id, customer_id=customer.customer_id)

    # Step F (Spoken Feedback Generation)
    hindi_words = sarvam.number_to_hindi_words(amount)
    confirmation_text = f"{customer.display_name} ji ke khate mein {hindi_words} rupaye jod diye gaye hain."

    try:
        tts_audio_bytes = sarvam.synthesize_speech(text=confirmation_text)
        confirmation_audio_b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
    except Exception:
        # Fallback to empty string if TTS service call fails/unreachable
        confirmation_audio_b64 = ""

    # Step G: Return response matching contract
    return {
        "txn_id": txn.txn_id,
        "customer_id": customer.customer_id,
        "new_balance": float(new_balance),
        "transcript": raw_transcript,
        "extracted": {
            "customer_name": customer.display_name,
            "amount": float(txn.amount),
            "items": extracted.get("items", []),
            "confidence": confidence
        },
        "confirmation_audio_text": confirmation_text,
        "confirmation_audio_b64": confirmation_audio_b64
    }
