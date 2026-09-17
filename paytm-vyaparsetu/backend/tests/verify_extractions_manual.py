import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extraction import extract_entities

test_samples = [
    # Clean Kirana credit entries (Should have high confidence >= 0.85)
    "suresh ji 240 ka dahi",
    "suresh 60 rupaye bread",
    "ramesh ko 150 rupaye udhaar likho",
    "vikas 300 rupaye tel aur sabun",
    "sharma ji ka 500 ka ghee baki hai",
    "anil 120 rupaye atta",
    "rahul 45 rupaye packet biscuit",
    "priya 80 rupaye doodh",
    "mukesh ko do sau chalis rupaye udhaar do",
    "rohit 1000 rupaye masale",
    
    # Missing info or ambiguous entries (Should have moderate confidence <= 0.5)
    "500 rupaye de diye",                    # No customer name
    "suresh ko samaan diya",                 # No amount
    "dahi aur doodh ka kitna hua",           # Pure query, no credit transaction
    "ramesh ji kal aayenge",                 # Statement, no financial intent
    
    # Garbled / Noise / Non-credit text (Should have low confidence <= 0.4)
    "hello bhaiya kaise ho",
    "haan kal subah aana dukan par",
    "scanner kaam nahi kar raha hai",
    "arre bhai side hato",
    "dhanyawad",
    ""
]

print(f"{'TRANSCRIPT':<45} | {'NAME':<10} | {'AMOUNT':<8} | {'CONF':<6} | {'STATUS'}")
print("-" * 85)

for text in test_samples:
    res = extract_entities(text)
    name = str(res.get("customer_name") or "-")
    amt = str(res.get("amount") or 0.0)
    conf = res.get("confidence", 0.0)
    
    if conf >= 0.8:
        status = "✅ PASS (High)"
    elif conf <= 0.5 and (not res.get("customer_name") or not res.get("amount") or conf <= 0.4):
        status = "✅ PASS (Low Guard)"
    else:
        status = "⚠️ REVIEW"
        
    display_text = text if len(text) <= 42 else text[:39] + "..."
    print(f"{display_text:<45} | {name:<10} | {amt:<8} | {conf:<6.2f} | {status}")