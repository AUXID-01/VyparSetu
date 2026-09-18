# VyaparSetu — Challan Extraction: Schema Chain & Vision Tech Stack

*This extends (not replaces) the Challan section of the Master Schema doc. It exists because the current `invoice_line_items` (sku, quantity, unit_price) and `/challan/extract` response are too thin for the real range of challan formats — formal GST printouts, carbon-copy books, thermal POS rolls, dot-matrix continuous stationery, and handwritten scraps — each with different fields, different reliability, and different failure modes.*

---

## 1. Acknowledging the format landscape

Six real-world formats, unified into one `challan_type` enum:

| `challan_type` | Typical source | What it has that others don't |
|---|---|---|
| `FORMAL_GST` | Laser printout, Tally/Busy/Marg ERP | GSTIN, HSN codes, CGST/SGST/IGST, e-way bill, vehicle number, legally sequential challan number |
| `CARBON_COPY_BOOK` | Pink/yellow duplicate pad | Printed acknowledgement text, driver + storekeeper signature lines, stamped serial |
| `THERMAL_POS_ROLL` | Bluetooth mini-printer receipt | Abbreviated SKUs, returnable crate counts, QR code |
| `DOT_MATRIX_CONTINUOUS` | Tractor-feed green/white paper | Batch numbers, expiry dates, MRP vs PTR, faint/broken characters |
| `HANDWRITTEN_SCRAP` | Notebook paper, cardboard | Loose math, no column structure, handwritten UPI ID |
| `UNKNOWN` | Fallback | Used when the model can't confidently classify — always forces manual review regardless of confidence score |

Separately, a **`capture_medium`** field (`DIRECT_UPLOAD | CAMERA_PHOTO | WHATSAPP_FORWARD`) tracks *how* the image arrived, independent of the document's underlying format — a WhatsApp-forwarded photo of a formal GST challan is still `FORMAL_GST` in content, but needs the extra preprocessing a compressed, skewed, glare-lit photo requires. Keeping these two fields separate means preprocessing decisions and extraction-strategy decisions don't get tangled together.

---

## 2. The schema chain

Four stages, each with its own schema, each independently loggable and independently debuggable — same principle as the rest of the pipeline.

```
Raw image
   │
   ▼
[Stage A] Pillow preprocessing  →  PreprocessedImageMeta
   │
   ▼
[Stage B] Google Vision OCR grounding  →  OCRGroundingResult
   │
   ▼
[Stage C] Vision LLM structuring  →  ChallanExtractionResult   ← the rich schema, extends your reference doc
   │
   ▼
[Stage D] Merchant confirms/edits  →  ConfirmedChallanInput
   │
   ▼
Postgres write  →  invoices / invoice_line_items / invoice_packaging_adjustments
```

### Stage A — `PreprocessedImageMeta` (Pillow)

```python
class PreprocessedImageMeta(BaseModel):
    original_format: str          # 'JPEG', 'PNG'
    original_dimensions: tuple[int, int]
    was_rotated: bool             # EXIF auto-orient applied
    contrast_enhanced: bool       # applied for thermal/carbon fade
    resized_to: tuple[int, int]   # capped max dimension, controls vision LLM token cost
    grayscale_variant_created: bool  # a grayscale copy is generated alongside the color original —
                                      # grayscale often helps OCR, color often helps the LLM read context/handwriting,
                                      # so both are available downstream, not a single lossy choice made upfront
```
This stage never touches an API — it's pure local image processing, so it's free, fast, and the first thing to check in logs when extraction goes wrong ("was the image even legible after preprocessing?").

### Stage B — `OCRGroundingResult` (Google Cloud Vision)

```python
class OCRGroundingResult(BaseModel):
    full_text: str                # raw OCR dump, no structure
    text_blocks: list[dict]       # bounding-box-tagged fragments, useful for debugging misreads
    avg_confidence: float
    used: bool                    # see routing logic below — not every challan_type benefits equally from this stage
```
**Important nuance from the format landscape:** Google Vision's OCR is strong on printed text (`FORMAL_GST`, `CARBON_COPY_BOOK`, `DOT_MATRIX_CONTINUOUS`) and comparatively weaker on cursive handwriting (`HANDWRITTEN_SCRAP`). So this stage is genuinely useful as a grounding signal for four of the five formats, but for handwritten scraps it's run anyway (it's free at your volume) and passed along, while the vision LLM in Stage C is told explicitly not to over-trust it for that type.

### Stage C — `ChallanExtractionResult` (Vision LLM) — the core schema, extending your reference doc

```python
class LineItem(BaseModel):
    raw_text: str                     # exactly as written/printed — audit trail
    canonical_item_name: str          # normalized (e.g. "Dahi Pouch 200g" regardless of phonetic spelling)
    quantity: float
    unit: str                         # 'crates','pouches','kg','pcs' — free text, not an enum, formats vary too much
    unit_rate: float
    line_total: float
    hsn_code: str | None              # only present on FORMAL_GST / some DOT_MATRIX
    is_free_scheme: bool = False      # "buy 10 get 1 free" — line_total should be 0 when true
    item_confidence: float            # PER-LINE confidence, not just one blanket number —
                                       # a handwritten total can be clear while individual items are fuzzy, or vice versa

class PackagingAdjustment(BaseModel):
    # Returnable crate/jali deposits — kept SEPARATE from line_items so they can never
    # accidentally get summed into the invoice total (the exact edge case called out
    # in your reference doc)
    item_name: str                    # 'Milk Crates'
    direction: str                    # 'RECEIVED' | 'RETURNED'
    quantity: int

class PaymentHandle(BaseModel):
    handle_type: str                  # 'UPI' | 'PHONE' | 'BANK'
    value: str                        # 'amuldistributor@icici'

class TaxBreakdown(BaseModel):
    # All nullable — only FORMAL_GST / some CARBON_COPY_BOOK challans have these
    cgst: float | None = None
    sgst: float | None = None
    igst: float | None = None
    cess: float | None = None

class ChallanExtractionResult(BaseModel):
    challan_type: str                 # the enum from Section 1
    capture_medium: str
    challan_number: str | None
    challan_date: str | None
    distributor_name_raw: str
    distributor_gstin: str | None
    vehicle_number: str | None
    e_way_bill_number: str | None
    line_items: list[LineItem]
    packaging_adjustments: list[PackagingAdjustment] = []
    payment_handle: PaymentHandle | None
    subtotal: float
    tax: TaxBreakdown
    additional_charges: float = 0.0   # labor/hamali charges seen on carbon-copy mandi slips
    total_payable: float
    # Confidence is reported per-section, not one number — different parts of a
    # challan can be reliable while others aren't, and downstream logic (Section 3)
    # treats them differently
    metadata_confidence: float        # challan_number/date/distributor identity
    line_items_confidence: float      # the actual money math
    overall_confidence: float
```

### Stage D — `ConfirmedChallanInput`
Same shape as `ChallanExtractionResult`, minus the confidence fields, after the merchant has reviewed/edited on screen. This is what actually gets written to Postgres — never Stage C's raw output directly, per the "don't trust unconfirmed OCR" rule from the Phase 5 plan.

---

## 3. Extended Postgres schema

```sql
-- invoices: extended with fields that only some challan_types populate
ALTER TABLE invoices ADD COLUMN challan_type TEXT;              -- Section 1 enum
ALTER TABLE invoices ADD COLUMN capture_medium TEXT;
ALTER TABLE invoices ADD COLUMN challan_number TEXT;
ALTER TABLE invoices ADD COLUMN distributor_gstin TEXT;
ALTER TABLE invoices ADD COLUMN vehicle_number TEXT;
ALTER TABLE invoices ADD COLUMN payment_handle_type TEXT;
ALTER TABLE invoices ADD COLUMN payment_handle_value TEXT;      -- powers the one-tap payout prefill
ALTER TABLE invoices ADD COLUMN tax_cgst NUMERIC(10,2);
ALTER TABLE invoices ADD COLUMN tax_sgst NUMERIC(10,2);
ALTER TABLE invoices ADD COLUMN tax_igst NUMERIC(10,2);
ALTER TABLE invoices ADD COLUMN additional_charges NUMERIC(10,2) DEFAULT 0;

-- invoice_line_items: extended
ALTER TABLE invoice_line_items ADD COLUMN raw_text TEXT;
ALTER TABLE invoice_line_items ADD COLUMN unit TEXT;
ALTER TABLE invoice_line_items ADD COLUMN hsn_code TEXT;
ALTER TABLE invoice_line_items ADD COLUMN is_free_scheme BOOLEAN DEFAULT false;

-- NEW: packaging adjustments, deliberately separate from line_items
CREATE TABLE invoice_packaging_adjustments (
    adjustment_id   TEXT PRIMARY KEY,      -- 'pkg_xxxxxx'
    invoice_id      TEXT NOT NULL REFERENCES invoices(invoice_id),
    item_name       TEXT NOT NULL,
    direction       TEXT NOT NULL,         -- 'RECEIVED' | 'RETURNED'
    quantity        INT NOT NULL
);

-- NEW: raw extraction audit trail — since this is financial data, keep the full
-- machine-readable trail per invoice, not just logs, in case of a later dispute
CREATE TABLE invoice_extraction_audit (
    audit_id            TEXT PRIMARY KEY,   -- 'aud_xxxxxx'
    invoice_id          TEXT NOT NULL REFERENCES invoices(invoice_id),
    ocr_raw_text         TEXT,
    vision_llm_raw_response JSONB NOT NULL,
    model_used           TEXT NOT NULL,     -- e.g. 'groq/llama-3.2-vision', 'gpt-4o'
    escalated            BOOLEAN DEFAULT false,
    merchant_edited_fields TEXT[],          -- which fields the merchant changed vs. what was extracted —
                                             -- track this over time, it tells you which challan_types need prompt work
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 4. Tech stack — with reasoning, not just a list

| Tool | Role | Why |
|---|---|---|
| **Pillow** | Stage A preprocessing: EXIF auto-rotate, contrast/sharpness enhancement, resize cap, grayscale variant generation | Free, local, no API call, and it's the first lever to pull when a WhatsApp-forwarded photo is dark/skewed/compressed — fixing it here is cheaper than hoping a vision model reads through it |
| **Google Cloud Vision (Document Text Detection)** | Stage B grounding OCR | Free for 1,000 units/month, strong on printed/dot-matrix/thermal text, gives you a second independent read of the numbers to cross-check against the LLM's — genuinely useful for 4 of 5 challan types, run-but-discount for handwritten |
| **Groq-hosted vision model** (Llama 3.2 Vision or current equivalent on Groq) | Stage C, **primary/default** structuring pass | Fast and cheap — good default for the common case (clean carbon-copy, ERP printouts, most thermal rolls) where your credits should go furthest |
| **GPT-4o or Claude vision** | Stage C, **escalation only** | Reserved for the harder cases — see routing logic below — since these cost more per call and your credits/budget should be spent where they matter |
| ~~Sarvam~~ | Not used here | Sarvam is audio-only (STT/TTS) — it has no role in the image pipeline; don't be tempted to route challan text through it |

**Routing/escalation logic — this is what makes "accurate" and "credit-conscious" compatible goals, not competing ones:**

```
1. Always run Stage A (Pillow) + Stage B (Google Vision OCR) — both cheap/free.
2. Run Stage C with the Groq vision model FIRST, passing both the preprocessed
   image AND the OCR grounding text as context (cross-referencing reduces
   hallucinated numbers on both sides).
3. Escalate to GPT-4o/Claude vision for a second pass ONLY IF:
   - overall_confidence < 0.75, OR
   - challan_type == 'HANDWRITTEN_SCRAP' (the hardest category, worth the
     extra cost every time), OR
   - total_payable > a merchant-configurable threshold (e.g. ₹5,000) — a
     high-value invoice is worth the extra accuracy spend regardless of
     reported confidence
4. If Groq's and the escalated model's totals disagree by more than a small
   tolerance (e.g. ₹5), force manual review regardless of either confidence
   score — a disagreement between two independent models is itself a signal,
   arguably a stronger one than either model's self-reported confidence.
5. Log which path was taken (Section's invoice_extraction_audit.escalated
   field) — over the hackathon this becomes real data on which challan_types
   actually needed the expensive model, useful both for the demo story and
   for tuning the threshold.
```

This also gives you a genuinely good demo narrative: *"most challans are read by a fast, cheap model in under two seconds — the system only reaches for a stronger model when the money or the confidence justifies it."* That's a more sophisticated pitch than "we call GPT-4o on every photo."

---

## 5. What this changes about the `/challan/extract` and `/challan/confirm` endpoints

The request/response shapes in the master schema doc's API contract need to grow to carry the fuller `ChallanExtractionResult`/`ConfirmedChallanInput` shape instead of the flat version — endpoints and status codes stay the same, only the payload richness changes. Since you asked to leave the master schema file as-is for now, this doc stands separately until you're ready to fold it in — happy to do that merge, or hand you the exact diff, whenever you say go.
