import re
from typing import Dict, Any

# Map Devanagari digits to ASCII digits
DEVANAGARI_DIGITS_TRANS = str.maketrans('०१२३४५६७८९', '0123456789')

# Hindi Devanagari number words map
HINDI_NUMBER_WORDS = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    "सौ": 100, "हजार": 1000, "हज़ार": 1000, "लाख": 100000
}

CURRENCY_WORDS = {
    "रुपये", "रुपया", "रुपए", "rupaye", "rupee", "rupees", "rs", "inr", "₹"
}

# Honorifics & Stopwords in both Latin (Hinglish) and Devanagari script
HONORIFICS_AND_STOPWORDS = {
    # Hinglish / Latin
    "ji", "bhai", "bhaiya", "saab", "uncle", "ko", "ke", "ka", "ki",
    "rupaye", "rupayee", "rupee", "rupees", "rs", "inr", "diya", "diye",
    "liya", "liye", "jod", "jodo", "do", "ek", "mein", "se", "ne",
    "de", "gaya", "gaye", "hai", "hain", "kal", "aana", "haan", "hello",
    "baki", "hai", "ko", "dokan", "dukan", "khata", "khate",
    # Devanagari
    "जी", "के", "का", "की", "को", "में", "खाता", "खाते", "रुपये", "रुपया", "रुपए",
    "डाल", "लिख", "दे", "दिया", "दिए", "दी", "कर", "दो", "दुकान", "उधार", "उधारो", "उधारी",
    "वाला", "वाली", "वाले", "बैलेंस", "जोड़", "जोड़", "जोड़ो", "जोड़ो", "बाकी", "है", "हैं",
    "सबुन", "सामान", "सामा"
}

KNOWN_ITEMS = [
    "dahi", "bread", "milk", "doodh", "oil", "refined oil", "butter",
    "biscuit", "cheeni", "chawal", "atta", "sabun", "paneer", "dhal", "dal",
    "दही", "ब्रेड", "दूध", "तेल", "मसाले", "घी", "अट्टा", "साबुन", "पनीर", "दाल"
]

def parse_hindi_number_words(tokens: list[str]) -> float:
    """
    Parses Hindi Devanagari number words (e.g. ['तीन', 'सौ', 'चालीस'] -> 340.0)
    Stops parsing if currency words (e.g. रुपये) are encountered to prevent trailing verbs like "दो" from acting as number 2.
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


def extract_entities(transcript: str) -> Dict[str, Any]:
    """
    Parses conversational Kirana credit transcripts (Devanagari, Hinglish, or English)
    into structured JSON.
    """
    raw_text = transcript.strip()
    if not raw_text:
        return {
            "customer_name": "",
            "amount": 0.0,
            "items": [],
            "confidence": 0.0
        }

    # Normalize Devanagari digits to ASCII digits
    normalized_text = raw_text.translate(DEVANAGARI_DIGITS_TRANS)
    text_lower = normalized_text.lower()

    # 1. Extract numeric amount
    amount = 0.0
    amounts = re.findall(r'\b\d+(?:\.\d+)?\b', text_lower)
    if amounts:
        amount = float(amounts[0])
    else:
        # Try parsing Hindi number words (e.g., "तीन सौ चालीस")
        tokens = re.findall(r'[\u0900-\u097F]+|[a-zA-Z]+', text_lower)
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

    customer_name = filtered_name_tokens[0] if filtered_name_tokens else ""

    # 4. Compute confidence score
    has_customer = bool(customer_name)
    has_valid_amount = amount > 0

    if has_customer and has_valid_amount:
        confidence = 0.92
    elif has_valid_amount and not has_customer:
        confidence = 0.45
    else:
        confidence = 0.20

    return {
        "customer_name": customer_name,
        "amount": amount,
        "items": extracted_items,
        "confidence": confidence
    }
