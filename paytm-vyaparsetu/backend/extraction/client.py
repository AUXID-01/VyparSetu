import json
import re
from typing import Dict, Any
from groq import Groq
from config import settings
from core.logging import get_logger
from extraction.prompts import EXTRACTION_SYSTEM_PROMPT

logger = get_logger("extraction.client")

# Cached sync Groq client for extraction
_groq_client = None

def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client

def _regex_fallback_extract(transcript: str) -> Dict[str, Any]:
    """Lightweight fallback if LLM is unavailable."""
    text_lower = transcript.strip().lower()
    amounts = re.findall(r'\b\d+(?:\.\d+)?\b', text_lower)
    amount = float(amounts[0]) if amounts else 0.0
    
    # Simple word tokenization excluding common words
    tokens = [w for w in re.findall(r'[a-zA-Z]+', text_lower) if w not in {"ka", "ko", "ke", "ki", "mein", "likho", "diya", "rupaye", "rs", "inr"}]
    customer = tokens[0] if tokens else ""
    
    return {
        "customer_name": customer,
        "amount": amount,
        "items": [],
        "confidence": 0.5 if (customer and amount > 0) else 0.2,
        "detected_language": "hi-IN"
    }

def extract_entities(transcript: str, request_id: str = "N/A") -> Dict[str, Any]:
    """
    Parses conversational Kirana credit transcripts in any Indian language/script
    into standardized English Latin structured JSON using Groq.
    """
    logger.info(f"[{request_id}] extraction_start: transcript='{transcript}'")
    raw_text = transcript.strip()
    if not raw_text:
        res = {
            "customer_name": "",
            "amount": 0.0,
            "items": [],
            "confidence": 0.0,
            "detected_language": "hi-IN"
        }
        logger.info(f"[{request_id}] extraction_complete (empty transcript): {res}")
        return res

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": raw_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Clean and normalize fields
        raw_name = str(data.get("customer_name") or "").strip().lower()
        amount = float(data.get("amount") or 0.0)
        items = [str(item).strip().lower() for item in data.get("items") or [] if str(item).strip()]
        confidence = float(data.get("confidence") or 0.0)
        detected_language = str(data.get("detected_language") or "hi-IN").strip()

        result = {
            "customer_name": raw_name,
            "amount": amount,
            "items": items,
            "confidence": confidence,
            "detected_language": detected_language
        }
        logger.info(f"[{request_id}] extraction_complete: customer='{raw_name}', amount={amount}, items={items}, confidence={confidence}")
        return result

    except Exception as exc:
        logger.warning(f"[{request_id}] Groq extraction failed ({exc}). Falling back to regex parser.")
        fallback = _regex_fallback_extract(raw_text)
        logger.info(f"[{request_id}] fallback_extraction_complete: {fallback}")
        return fallback
