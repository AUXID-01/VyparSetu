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
    
    try:
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
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] DB transaction failed during process_log_credit: {e}")
        raise
    
    # Confirmation text
    confirmation_text = f"{customer.display_name} ji ke khate mein {amount} rupaye jod diye gaye hain."
    
    return {
        "txn_id": txn.txn_id,
        "customer_id": customer.customer_id,
        "new_balance": float(current_balance),
        "confirmation_audio_text": confirmation_text
    }


def create_confirmation_token(merchant_id: str, payload: dict) -> str:
    import jwt, datetime
    from config import settings
    token_data = {
        "merchant_id": merchant_id,
        "payload": payload,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    }
    return jwt.encode(token_data, settings.VOICE_CONFIRMATION_SECRET, algorithm="HS256")

def decode_confirmation_token(token: str) -> dict:
    import jwt
    from config import settings
    try:
        decoded = jwt.decode(token, settings.VOICE_CONFIRMATION_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise AppException(code=ErrorCode.INTERNAL_TOKEN_INVALID, message="Token expired", status_code=400)
    except jwt.InvalidTokenError:
        raise AppException(code=ErrorCode.INTERNAL_TOKEN_INVALID, message="Invalid token", status_code=400)


def confirm_credit(db: Session, merchant_id: str, token: str, confirmed: bool, request_id: str = "N/A") -> dict:
    logger.info(f"[{request_id}] confirm_credit start: merchant_id='{merchant_id}', confirmed={confirmed}")
    
    try:
        decoded = decode_confirmation_token(token)
    except AppException as e:
        logger.warning(f"[{request_id}] Invalid/expired token: {e.message}")
        return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}

    if decoded["merchant_id"] != merchant_id:
        logger.warning(f"[{request_id}] Token merchant_id mismatch")
        return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}

    payload = decoded["payload"]
    
    if not confirmed:
        logger.info(f"[{request_id}] User rejected best-guess: {payload}")
        return {"outcome": "DISCARDED"}

    customer_name = payload["customer_name"]
    amount = float(payload["amount"])
    items = payload.get("items", [])
    confidence = payload["confidence"]
    raw_transcript = payload.get("raw_transcript", "")

    # Perform the exact same atomic write path
    try:
        customer = customers_repo.resolve_or_create(db, merchant_id=merchant_id, display_name=customer_name)
    
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
    
        new_balance = ledger_repo.calculate_customer_due(db, merchant_id=merchant_id, customer_id=customer.customer_id)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] DB transaction failed during confirm_credit: {e}")
        raise

    # TTS Feedback
    formatted_amount = sarvam.format_inr_text(amount)
    confirmation_text = f"{customer.display_name} ji ke khate mein {formatted_amount} rupaye jod diye gaye hain."
    
    try:
        tts_audio_bytes = sarvam.synthesize_speech(text=confirmation_text, request_id=request_id)
        confirmation_audio_b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
        confirmation_audio_status = "AVAILABLE"
    except Exception as exc:
        logger.error(f"[{request_id}] Stage 6 Exception: TTS synthesis failed ({exc}), setting audio to null")
        confirmation_audio_b64 = None
        confirmation_audio_status = "UNAVAILABLE"

    return {
        "outcome": "CONFIRMED",
        "txn_id": txn.txn_id,
        "customer_id": customer.customer_id,
        "new_balance": float(new_balance),
        "transcript": raw_transcript,
        "extracted": {
            "customer_name": customer.display_name,
            "amount": float(txn.amount),
            "items": items,
            "confidence": confidence
        },
        "confirmation_audio_text": confirmation_text,
        "confirmation_audio_b64": confirmation_audio_b64,
        "confirmation_audio_status": confirmation_audio_status
    }


def process_voice_credit_audio(
    db: Session,
    merchant_id: str,
    audio_bytes: bytes,
    language_override: str = None,
    filename: str = "audio.wav",
    request_id: str = "N/A"
) -> dict:
    """
    Full counter-speed voice credit pipeline:
    Audio Upload -> Sarvam STT -> Extraction -> Low Confidence Guard -> Postgres DB -> Number-to-Words -> Sarvam TTS -> Spoken Audio & JSON
    """
    logger.info(f"[{request_id}] process_voice_credit_audio start: merchant_id='{merchant_id}', filename='{filename}', size={len(audio_bytes)} bytes")

    # Resolve language
    from db.repositories import merchants_repo
    merchant = merchants_repo.get_merchant_by_id(db, merchant_id)
    if not merchant:
        raise AppException(
            code=ErrorCode.MERCHANT_NOT_FOUND,
            message="Merchant not found",
            status_code=404
        )
    
    stt_lang = language_override if language_override else merchant.preferred_language

    try:
        # Step A (Input Guard)
        if len(audio_bytes) < 1000:
            logger.warning(f"[{request_id}] Stage 1 Guard Failed: clip size {len(audio_bytes)} < 1000 bytes")
            return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}
    
        # Step B (STT)
        stt_res = sarvam.transcribe_audio(audio_bytes=audio_bytes, filename=filename, request_id=request_id, language=stt_lang)
        raw_transcript = stt_res.get("transcript", "")
        if not raw_transcript.strip():
            logger.warning(f"[{request_id}] Stage 2 Failed: empty raw transcript returned from STT")
            return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}
    
        # Step C (Extraction)
        extracted = extraction.extract_entities(raw_transcript, request_id=request_id)
    except (AppException, Exception) as e:
        logger.warning(f"[{request_id}] Pipeline failure during STT/Extraction: {e}")
        return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}

    # Step D (Confidence Guard)
    confidence = extracted.get("confidence", 0.0)
    customer_name = extracted.get("customer_name")
    amount = float(extracted.get("amount", 0.0))
    items = extracted.get("items", [])

    if not customer_name or amount <= 0:
        return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}

    if confidence < 0.40:
        logger.warning(f"[{request_id}] Stage 4 Guard Failed: confidence={confidence} < 0.40")
        return {"outcome": "FAILED_RETRY", "message": "Please repeat your entry."}
        
    if confidence < 0.75:
        # 0.40 <= confidence < 0.75 -> NEEDS_CONFIRMATION
        logger.info(f"[{request_id}] Confidence {confidence} in HITL band [0.40, 0.75). Requesting confirmation.")
        token = create_confirmation_token(merchant_id, {
            "customer_name": customer_name,
            "amount": amount,
            "items": items,
            "confidence": confidence,
            "raw_transcript": raw_transcript
        })
        return {
            "outcome": "NEEDS_CONFIRMATION",
            "best_guess": {
                "customer_name": customer_name,
                "amount": amount,
                "items": items,
                "confidence": confidence
            },
            "confirmation_token": token
        }

    # Step E (Database Ledger Invariants)
    # confidence >= 0.75 -> CONFIRMED
    logger.info(f"[{request_id}] Stage 5 (Database Writes): resolving customer and inserting transaction...")
    try:
        customer = customers_repo.resolve_or_create(db, merchant_id=merchant_id, display_name=customer_name)
    
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
    
        new_balance = ledger_repo.calculate_customer_due(db, merchant_id=merchant_id, customer_id=customer.customer_id)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[{request_id}] DB transaction failed during process_voice_credit_audio: {e}")
        raise

    # Step F (Spoken Feedback Generation)
    formatted_amount = sarvam.format_inr_text(amount)
    confirmation_text = f"{customer.display_name} ji ke khate mein {formatted_amount} rupaye jod diye gaye hain."
    logger.info(f"[{request_id}] Stage 6 (Spoken Audio TTS): formatted spoken text='{confirmation_text}'")

    try:
        tts_audio_bytes = sarvam.synthesize_speech(text=confirmation_text, request_id=request_id)
        confirmation_audio_b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
        confirmation_audio_status = "AVAILABLE"
        logger.info(f"[{request_id}] Stage 6 Result: TTS audio generated ({len(tts_audio_bytes)} bytes, b64_len={len(confirmation_audio_b64)})")
    except Exception as exc:
        logger.error(f"[{request_id}] Stage 6 Exception: TTS synthesis failed ({exc}), setting audio to null")
        confirmation_audio_b64 = None
        confirmation_audio_status = "UNAVAILABLE"

    # Step G: Return response matching contract
    logger.info(f"[{request_id}] Voice pipeline execution completed successfully for merchant='{merchant_id}'")
    return {
        "outcome": "CONFIRMED",
        "txn_id": txn.txn_id,
        "customer_id": customer.customer_id,
        "new_balance": float(new_balance),
        "transcript": raw_transcript,
        "extracted": {
            "customer_name": customer.display_name,
            "amount": float(txn.amount),
            "items": items,
            "confidence": confidence
        },
        "confirmation_audio_text": confirmation_text,
        "confirmation_audio_b64": confirmation_audio_b64,
        "confirmation_audio_status": confirmation_audio_status
    }

