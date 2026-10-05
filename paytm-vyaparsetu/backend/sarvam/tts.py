import base64
import httpx
from .client import get_sarvam_headers, SARVAM_BASE_URL
from core.logging import get_logger

logger = get_logger("sarvam.tts")

def format_inr_text(amount: float | int) -> str:
    """
    Formats numeric values into raw passthrough text for TTS.
    Returns strings like '100', '1000', '1,00,000', '150.50'.
    """
    amount_float = float(amount)
    s = f"{amount_float:.2f}"
    int_part, dec_part = s.split('.')
    
    if len(int_part) > 3:
        res = "," + int_part[-3:]
        int_part = int_part[:-3]
        while len(int_part) > 2:
            res = "," + int_part[-2:] + res
            int_part = int_part[:-2]
        res = int_part + res
        
        # Format 4-digit numbers without comma (e.g. 1000 instead of 1,000)
        if len(res) == 5 and res[1] == ',':
            res = res.replace(",", "")
    else:
        res = int_part
        
    if dec_part == "00":
        return res
    
    return f"{res}.{dec_part}"


def synthesize_speech(text: str, target_language_code: str = "hi-IN", speaker: str = "ritu", request_id: str = "N/A") -> bytes:
    """
    Synthesizes text into raw audio bytes using Sarvam AI Text-to-Speech API (bulbul:v3).
    """
    logger.info(f"[{request_id}] Sarvam TTS synthesis request: text='{text}', target_language_code='{target_language_code}', speaker='{speaker}'")
    url = f"{SARVAM_BASE_URL}/text-to-speech"
    headers = get_sarvam_headers()
    
    # Sarvam bulbul:v3 enforces max 500 characters per input
    input_text = text.strip()
    if len(input_text) > 480:
        trimmed = input_text[:480]
        last_punct = max(trimmed.rfind('.'), trimmed.rfind('\n'), trimmed.rfind('।'))
        if last_punct > 100:
            input_text = trimmed[:last_punct + 1].strip()
        else:
            input_text = trimmed.strip()

    payload = {
        "inputs": [input_text],
        "target_language_code": target_language_code,
        "speaker": speaker,
        "model": "bulbul:v3",
    }
    
    with httpx.Client(timeout=30.0) as client:
        try:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            res_json = response.json()
            audio_b64 = res_json["audios"][0]
            audio_bytes = base64.b64decode(audio_b64)
            logger.info(f"[{request_id}] Sarvam TTS synthesis completed: bytes={len(audio_bytes)}")
            return audio_bytes
        except httpx.HTTPError as exc:
            raw_response = exc.response.text if hasattr(exc, "response") and exc.response else "No response body"
            logger.error(f"[{request_id}] Sarvam TTS API call failed: {exc} | Raw Response: {raw_response}")
            raise

