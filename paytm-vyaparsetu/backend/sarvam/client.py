import httpx
from config import settings

SARVAM_BASE_URL = "https://api.sarvam.ai"

def get_sarvam_headers() -> dict:
    return {
        "api-subscription-key": settings.SARVAM_API_KEY
    }

def get_sarvam_client(timeout: float = 30.0) -> httpx.Client:
    return httpx.Client(
        base_url=SARVAM_BASE_URL,
        headers=get_sarvam_headers(),
        timeout=timeout,
    )
