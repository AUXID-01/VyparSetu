from .client import get_sarvam_client, get_sarvam_headers, SARVAM_BASE_URL
import httpx
from core.errors import AppException, ErrorCode
from core.logging import get_logger

logger = get_logger("sarvam.stt")

LANGUAGE_MAPPING = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
    "od": "od-IN",
    "en": "en-IN"
}

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav", request_id: str = "N/A", language: str = "hi") -> dict:
    """
    Transcribes audio bytes into text using Sarvam AI Speech-to-Text API (saaras:v3 codemix).
    """
    logger.info(f"[{request_id}] STT input received: filename='{filename}', size={len(audio_bytes)} bytes, lang='{language}'")
    
    url = f"{SARVAM_BASE_URL}/speech-to-text"
    headers = get_sarvam_headers()
    
    mime_type = "audio/webm" if filename.endswith(".webm") else "audio/wav"
    files = {"file": (filename, audio_bytes, mime_type)}
    
    mapped_lang = LANGUAGE_MAPPING.get(language)
    if not mapped_lang:
        raise AppException(
            code="UNSUPPORTED_LANGUAGE",
            message=f"Unsupported STT language code: '{language}'",
            status_code=400
        )
        
    data = {
        "model": "saaras:v3",
        "mode": "codemix",
        "language_code": mapped_lang,
    }
    
    with httpx.Client(timeout=30.0) as client:
        try:
            logger.debug(f"[{request_id}] Calling Sarvam STT API endpoint: {url}")
            response = client.post(url, headers=headers, data=data, files=files)
            response.raise_for_status()
            res_json = response.json()
            
            transcript = res_json.get("transcript", "")
            language_code = res_json.get("language_code", "hi-IN")
            
            logger.info(f"[{request_id}] Sarvam STT raw response: transcript='{transcript}', language_code='{language_code}'")
            return {
                "transcript": transcript,
                "language_code": language_code,
            }
        except httpx.HTTPStatusError as exc:
            err_body = exc.response.text
            status = exc.response.status_code
            logger.error(f"[{request_id}] [Sarvam STT Error] Status: {status}, Body: {err_body}")
            msg = f"Sarvam STT API error ({status}): {err_body}"
            if status == 403:
                msg = "Sarvam STT Authentication failed (403). Please set a valid SARVAM_API_KEY in backend/.env"
            raise AppException(
                code=ErrorCode.SARVAM_API_ERROR,
                message=msg,
                status_code=400
            ) from exc
        except httpx.HTTPError as exc:
            logger.error(f"[{request_id}] [Sarvam STT Network Error] {str(exc)}")
            raise AppException(
                code=ErrorCode.SARVAM_API_ERROR,
                message=f"Sarvam STT network error: {str(exc)}",
                status_code=400
            ) from exc

