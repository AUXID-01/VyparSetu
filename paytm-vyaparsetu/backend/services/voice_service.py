import base64
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from db.repositories import customers_repo, ledger_repo, outbox_repo
from core.enums import TxnType, LedgerSource, OutboxEventType
from core.errors import AppException, ErrorCode
from core.logging import get_logger
from db.models import LedgerTransaction
import sarvam
import extraction

logger = get_logger("services.voice_service")

def process_log_credit(
    db: Session,
    merchant_id: str,
    customer_name: str,
    amount: float,
    items: list[str],
    confidence: float,
    request_id: str = "N/A"
) -> dict:
    logger.info(f"[{request_id}] process_log_credit start: merchant_id='{merchant_id}', customer_name='{customer_name}', amount={amount}, confidence={confidence}")
    
    # 1. Resolve/create customer
    customer = customers_repo.get_or_create(db, merchant_id, customer_name)
    logger.info(f"[{request_id}] Identity resolution: customer_id='{customer.customer_id}', display_name='{customer.display_name}', canonical_key='{customer.canonical_key}'")
    
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
    logger.info(f"[{request_id}] Ledger insert: txn_id='{txn.txn_id}', amount={txn.amount}")
    
    # 3. Insert outbox_events row
    event = outbox_repo.create_event(
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
    logger.info(f"[{request_id}] Outbox insert: event_id='{event.event_id}', status=PENDING (awaiting poller)")
    
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
    filename: str = "audio.wav",
    request_id: str = "N/A"
) -> dict:
    """
    Full counter-speed voice credit pipeline:
    Audio Upload -> Sarvam STT -> Extraction -> Low Confidence Guard -> Postgres DB -> Number-to-Words -> Sarvam TTS -> Spoken Audio & JSON
    """
    logger.info(f"[{request_id}] process_voice_credit_audio start: merchant_id='{merchant_id}', filename='{filename}', size={len(audio_bytes)} bytes")

    # Step A (Input Guard)
    logger.debug(f"[{request_id}] Stage 1 (Input Guard): checking audio clip size={len(audio_bytes)} bytes")
    if len(audio_bytes) < 1000:
        logger.warning(f"[{request_id}] Stage 1 Guard Failed: clip size {len(audio_bytes)} < 1000 bytes")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="Empty or inaudible voice clip",
            status_code=400
        )

    # Step B (STT)
    logger.info(f"[{request_id}] Stage 2 (Sarvam STT): transcribing audio clip...")
    stt_res = sarvam.transcribe_audio(audio_bytes=audio_bytes, filename=filename, request_id=request_id)
    raw_transcript = stt_res.get("transcript", "")
    logger.info(f"[{request_id}] Stage 2 Result: raw_transcript='{raw_transcript}'")
    if not raw_transcript.strip():
        logger.warning(f"[{request_id}] Stage 2 Failed: empty raw transcript returned from STT")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message="No clear speech detected",
            status_code=400
        )

    # Step C (Extraction)
    logger.info(f"[{request_id}] Stage 3 (NLP Extraction): extracting entities from raw transcript...")
    extracted = extraction.extract_entities(raw_transcript, request_id=request_id)

    # Step D (Confidence Guard)
    confidence = extracted.get("confidence", 0.0)
    customer_name = extracted.get("customer_name")
    amount = float(extracted.get("amount", 0.0))

    logger.info(f"[{request_id}] Stage 3 Result: customer_name='{customer_name}', amount={amount}, confidence={confidence}")
    if confidence < 0.6 or not customer_name or amount <= 0:
        logger.warning(f"[{request_id}] Stage 4 Guard Failed: confidence={confidence} < 0.6, customer_name='{customer_name}', amount={amount}")
        raise AppException(
            code=ErrorCode.LOW_CONFIDENCE_EXTRACTION,
            message=f"Could not reliably extract credit details from: '{raw_transcript}'",
            status_code=400
        )

    # Step E (Database Ledger Invariants)
    logger.info(f"[{request_id}] Stage 5 (Database Writes): resolving customer and inserting transaction...")
    customer = customers_repo.resolve_or_create(db, merchant_id=merchant_id, display_name=customer_name)
    logger.info(f"[{request_id}] Resolved customer: customer_id='{customer.customer_id}', canonical_key='{customer.canonical_key}'")

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
    logger.info(f"[{request_id}] Inserted ledger transaction: txn_id='{txn.txn_id}', amount={txn.amount}")

    outbox_evt = outbox_repo.create_outbox_event(
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
    logger.info(f"[{request_id}] Inserted outbox event: event_id='{outbox_evt.event_id}', status=PENDING (awaiting poller)")

    new_balance = ledger_repo.calculate_customer_due(db, merchant_id=merchant_id, customer_id=customer.customer_id)
    logger.info(f"[{request_id}] Calculated updated balance: customer_id='{customer.customer_id}', new_balance={new_balance}")

    # Step F (Spoken Feedback Generation)
    hindi_words = sarvam.number_to_hindi_words(amount)
    confirmation_text = f"{customer.display_name} ji ke khate mein {hindi_words} rupaye jod diye gaye hain."
    logger.info(f"[{request_id}] Stage 6 (Spoken Audio TTS): formatted spoken text='{confirmation_text}'")

    try:
        tts_audio_bytes = sarvam.synthesize_speech(text=confirmation_text, request_id=request_id)
        confirmation_audio_b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
        logger.info(f"[{request_id}] Stage 6 Result: TTS audio generated ({len(tts_audio_bytes)} bytes, b64_len={len(confirmation_audio_b64)})")
    except Exception as exc:
        logger.warning(f"[{request_id}] Stage 6 Exception: TTS synthesis failed ({exc}), setting b64 to empty string")
        confirmation_audio_b64 = ""

    # Step G: Return response matching contract
    logger.info(f"[{request_id}] Voice pipeline execution completed successfully for merchant='{merchant_id}'")
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

