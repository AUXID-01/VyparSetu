import re
from typing import Dict, Any

# Map Devanagari digits to ASCII digits
DEVANAGARI_DIGITS_TRANS = str.maketrans('०१२३४५६७८९', '0123456789')

# Hindi & Hinglish number words map
HINDI_NUMBER_WORDS = {
    # Devanagari
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    "सौ": 100, "हजार": 1000, "हज़ार": 1000, "लाख": 100000,
    
    # Hinglish / Latin Transliterations
    "ek": 1, "do": 2, "doo": 2, "teen": 3, "tin": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5,
    "chhah": 6, "che": 6, "chhe": 6, "saat": 7, "sat": 7, "aath": 8, "ath": 8, "nau": 9, "no": 9, "das": 10,
    "gyarah": 11, "barah": 12, "baarah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16, "satrah": 17,
    "atharah": 18, "unnees": 19, "bees": 20, "tees": 30, "chalis": 40, "chaalis": 40, "pachas": 50, "saath": 60, "sath": 60,
    "sattar": 70, "assi": 80, "nabbe": 90,
    "sau": 100, "so": 100, "hazaar": 1000, "hazar": 1000, "lakh": 100000, "lac": 100000
}

CURRENCY_WORDS = {
    "रुपये", "रुपया", "रुपए", "rupaye", "rupee", "rupees", "rs", "inr", "₹"
}

# Honorifics & Stopwords in both Latin (Hinglish) and Devanagari script
HONORIFICS_AND_STOPWORDS = {
    # Hinglish / Latin
    "ji", "bhai", "bhaiya", "saab", "uncle", "ko", "ke", "ka", "ki",
    "rupaye", "rupayee", "rupee", "rupees", "rs", "inr", "diya", "diye",
    "liya", "liye", "jod", "jodo", "do", "ek", "mein", "me", "se", "ne",
    "de", "gaya", "gaye", "hai", "hain", "kal", "aana", "haan", "hello",
    "baki", "dokan", "dukan", "khata", "khate", "likh", "likhlo", "lo", "aur",
    "par", "pe", "se", "naam", "naama",
    # Devanagari
    "जी", "के", "का", "की", "को", "में", "खाता", "खाते", "रुपये", "रुपया", "रुपए",
    "डाल", "लिख", "लो", "दे", "दिया", "दिए", "दी", "कर", "दो", "दुकान", "उधार", "उधारो", "उधारी",
    "वाला", "वाली", "वाले", "बैलेंस", "जोड़", "जोड़", "जोड़ो", "जोड़ो", "बाकी", "है", "हैं",
    "और"
}

KNOWN_ITEMS = [
    "dahi", "bread", "milk", "doodh", "oil", "refined oil", "butter",
    "biscuit", "cheeni", "chawal", "atta", "aata", "sabun", "paneer", "dhal", "dal",
    "tel", "ghee", "ghe", "masala", "masale", "chai", "patti", "namak",
    "दही", "ब्रेड", "दूध", "तेल", "मसाले", "घी", "अट्टा", "साबुन", "पनीर", "दाल"
]

def parse_hindi_number_words(tokens: list[str]) -> float:
    """
    Parses Hindi/Hinglish number words (e.g. ['do', 'sau', 'chalis'] -> 240.0, ['तीन', 'सौ', 'चालीस'] -> 340.0)
    Stops parsing if currency words (e.g. रुपये / rupaye) are encountered to prevent trailing verbs.
    """
    total = 0.0
    current = 0.0
    found_any = False
    
    for token in tokens:
        if token in CURRENCY_WORDS:
            # Stop parsing Hindi number words once currency indicator is reached
            break
        if token in HINDI_NUMBER_WORDS:
            val = HINDI_NUMBER_WORDS[token]
            found_any = True
            if val in (100, 1000, 100000):
                if current == 0:
                    current = 1
                current *= val
                if val >= 1000:
                    total += current
                    current = 0
            else:
                current += val
    total += current
    return total if found_any else 0.0


from core.logging import get_logger

logger = get_logger("extraction.client")

def extract_entities(transcript: str, request_id: str = "N/A") -> Dict[str, Any]:
    """
    Parses conversational Kirana credit transcripts (Devanagari, Hinglish, or English)
    into structured JSON.
    """
    logger.info(f"[{request_id}] extraction_start: transcript='{transcript}'")
    raw_text = transcript.strip()
    if not raw_text:
        res = {
            "customer_name": "",
            "amount": 0.0,
            "items": [],
            "confidence": 0.0
        }
        logger.info(f"[{request_id}] extraction_complete (empty transcript): {res}")
        return res

    # Normalize Devanagari digits to ASCII digits
    normalized_text = raw_text.translate(DEVANAGARI_DIGITS_TRANS)
    text_lower = normalized_text.lower()

    # 1. Extract numeric amount
    amount = 0.0
    amounts = re.findall(r'\b\d+(?:\.\d+)?\b', text_lower)
    if amounts:
        amount = float(amounts[0])
    else:
        # Try parsing Hindi/Hinglish number words (e.g., "do sau chalis" or "तीन सौ चालीस")
        tokens = re.findall(r'[\u0900-\u097F]+|[a-zA-Z0-9]+', text_lower)
        amount = parse_hindi_number_words(tokens)

    # 2. Extract items
    extracted_items = []
    for item in KNOWN_ITEMS:
        if re.search(r'\b' + re.escape(item) + r'\b', text_lower):
            extracted_items.append(item)

    # 3. Extract customer name
    tokens = re.findall(r'[\u0900-\u097F]+|[a-zA-Z]+', text_lower)
    filtered_name_tokens = []

    for token in tokens:
        # Exclude stopwords, number words, and known items
        if (
            token in HONORIFICS_AND_STOPWORDS
            or token in KNOWN_ITEMS
            or token in HINDI_NUMBER_WORDS
            or token in CURRENCY_WORDS
        ):
            continue
        filtered_name_tokens.append(token)

    raw_name = filtered_name_tokens[0] if filtered_name_tokens else ""
    customer_name = raw_name.capitalize() if raw_name else ""

    # 4. Compute confidence score
    has_customer = bool(customer_name)
    has_valid_amount = amount > 0

    if has_customer and has_valid_amount:
        confidence = 0.92
    elif has_valid_amount and not has_customer:
        confidence = 0.45
    else:
        confidence = 0.20

    res = {
        "customer_name": customer_name,
        "amount": amount,
        "items": extracted_items,
        "confidence": confidence
    }
    logger.info(f"[{request_id}] extraction_complete: customer='{customer_name}', amount={amount}, items={extracted_items}, confidence={confidence}")
    return res

