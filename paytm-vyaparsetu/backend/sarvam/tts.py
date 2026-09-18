import base64
import httpx
from .client import get_sarvam_headers, SARVAM_BASE_URL

# Hindi transliterated dictionary for numbers 1 to 99
HINDI_NUMBERS = {
    1: "ek", 2: "do", 3: "teen", 4: "chaar", 5: "paanch", 6: "chhah", 7: "saat", 8: "aath", 9: "nau", 10: "das",
    11: "gyarah", 12: "baarah", 13: "terah", 14: "chaudah", 15: "pandrah", 16: "solah", 17: "satrah", 18: "athtahrah", 19: "unnees", 20: "bees",
    21: "ikkees", 22: "baaees", 23: "teees", 24: "chaubees", 25: "pachees", 26: "chhabbees", 27: "sattaees", 28: "atthaees", 29: "untees", 30: "tees",
    31: "ikattees", 32: "battees", 33: "tentees", 34: "chauntees", 35: "paentees", 36: "chhattees", 37: "saintees", 38: "aththees", 39: "unchalis", 40: "chalis",
    41: "iktalis", 42: "byalis", 43: "tentalis", 44: "chawalis", 45: "paintalis", 46: "chhyalis", 47: "saintalis", 48: "adhtalis", 49: "unchas", 50: "pachas",
    51: "ikyawan", 52: "bawan", 53: "tirpan", 54: "chawwan", 55: "pachpawan", 56: "chhappan", 57: "sattawan", 58: "atthawan", 59: "unsath", 60: "saath",
    61: "iksath", 62: "baasath", 63: "tirsath", 64: "chaunsath", 65: "painsath", 66: "chhahsath", 67: "satsath", 68: "atthsath", 69: "unhattar", 70: "sattar",
    71: "ikhattar", 72: "bahattar", 73: "tihattar", 74: "chauhattar", 75: "pachhattar", 76: "chhihattar", 77: "sathattar", 78: "athattar", 79: "unasi", 80: "assi",
    81: "ikyasi", 82: "bayasi", 83: "tirasi", 84: "chaurasi", 85: "pachasi", 86: "chhiyasi", 87: "sattasi", 88: "atthasi", 89: "nawasi", 90: "nabbe",
    91: "ikyaneve", 92: "banve", 93: "tiranve", 94: "chauranve", 95: "pachchanve", 96: "chhiyanve", 97: "sattananve", 98: "atthananve", 99: "ninnanve"
}

def number_to_hindi_words(n: int | float) -> str:
    """
    Converts a numeric value up to 99,999 into transliterated Hindi words.
    Examples:
        50 -> "pachas"
        60 -> "saath"
        240 -> "do sau chalis"
        300 -> "teen sau"
        1500 -> "ek hazaar paanch sau"
    """
    val = int(round(n))
    if val <= 0:
        return "zero"

    parts = []

    # Thousands place
    thousands = val // 1000
    if thousands > 0:
        if thousands in HINDI_NUMBERS:
            parts.append(f"{HINDI_NUMBERS[thousands]} hazaar")
        val %= 1000

    # Hundreds place
    hundreds = val // 100
    if hundreds > 0:
        if hundreds in HINDI_NUMBERS:
            parts.append(f"{HINDI_NUMBERS[hundreds]} sau")
        val %= 100

    # Tens & Units place (1 to 99)
    if val > 0:
        if val in HINDI_NUMBERS:
            parts.append(HINDI_NUMBERS[val])

    return " ".join(parts)


def synthesize_speech(text: str, target_language_code: str = "hi-IN", speaker: str = "ritu") -> bytes:
    """
    Synthesizes text into raw audio bytes using Sarvam AI Text-to-Speech API (bulbul:v3).
    """
    url = f"{SARVAM_BASE_URL}/text-to-speech"
    headers = get_sarvam_headers()
    
    payload = {
        "inputs": [text],
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
            return base64.b64decode(audio_b64)
        except httpx.HTTPError:
            # Fallback for hackathon demo if API key is invalid/missing
            # Return a tiny 0-second valid WAV file
            silent_wav_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
            return base64.b64decode(silent_wav_b64)
