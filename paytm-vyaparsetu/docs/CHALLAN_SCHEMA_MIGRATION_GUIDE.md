# Paytm VyaparSetu — Challan Schema Extension & Database Migration Guide

This document provides a complete guide for the **Multi-Format Challan Schema Extension & Database Migration**, detailing all architecture changes, Stage A–D Pydantic schemas, database model updates, Alembic migration steps, and verification procedures.

---

## 1. Overview & Architecture

To support the full landscape of Kirana supplier document formats (**Formal GST**, **Carbon-Copy Pads**, **Thermal POS Receipts**, **Dot-Matrix Continuous Stationery**, and **Handwritten Mandi Scraps**), the database and vision processing stack were extended with a 4-Stage Schema Chain:

```
Raw Image Upload
   │
   ▼
[Stage A] Pillow Preprocessing  ──► PreprocessedImageMeta (dimensions, rotation, contrast, grayscale)
   │
   ▼
[Stage B] Google Vision OCR     ──► OCRGroundingResult (bounding box text fragments, avg_confidence)
   │
   ▼
[Stage C] Vision Structuring   ──► ChallanExtractionResult (rich schema: items, crates, tax, payment handles)
   │
   ▼
[Stage D] Merchant Confirmation ──► ConfirmedChallanInput (merchant-reviewed payload)
   │
   ▼
PostgreSQL Database Write     ──► invoices / invoice_line_items / invoice_packaging_adjustments / invoice_extraction_audit
```

---

## 2. Comprehensive Inventory of Code & Schema Changes

### 2.1 Stage A–D Pydantic Schemas (`backend/vision/schemas.py`)

Created [`backend/vision/schemas.py`](file:///c:/VyaparSetu/VyparSetu/paytm-vyaparsetu/backend/vision/schemas.py) defining:

1. **String Enums**:
   - `ChallanType`: `FORMAL_GST | CARBON_COPY_BOOK | THERMAL_POS_ROLL | DOT_MATRIX_CONTINUOUS | HANDWRITTEN_SCRAP | UNKNOWN`
   - `CaptureMedium`: `DIRECT_UPLOAD | CAMERA_PHOTO | WHATSAPP_FORWARD`
   - `PackagingDirection`: `RECEIVED | RETURNED`
   - `PaymentHandleType`: `UPI | PHONE | BANK`

2. **Stage A Schema (`PreprocessedImageMeta`)**:
   Tracks image dimensions, EXIF auto-rotation, contrast enhancements, max dimension scaling, and grayscale variant flags.

3. **Stage B Schema (`OCRGroundingResult`)**:
   Tracks bounding-box OCR fragments, full text string, and average confidence.

4. **Stage C Schemas (`ChallanExtractionResult`)**:
   - `LineItem`: `raw_text`, `canonical_item_name`, `quantity`, `unit`, `unit_rate`, `line_total`, `hsn_code`, `is_free_scheme`, `item_confidence`.
   - `PackagingAdjustment`: `item_name`, `direction` (`RECEIVED`/`RETURNED`), `quantity` *(tracks returnable crate/jali deposits separately so they never contaminate product totals)*.
   - `PaymentHandle`: `handle_type`, `value` *(powers 1-tap supplier payout prefill)*.
   - `TaxBreakdown`: `cgst`, `sgst`, `igst`, `cess`.
   - `ChallanExtractionResult`: Complete structured payload with per-section confidence scores (`metadata_confidence`, `line_items_confidence`, `overall_confidence`).

5. **Stage D Schema (`ConfirmedChallanInput`)**:
   Represents merchant-verified input ready for PostgreSQL insertion (confidence fields removed).

---

### 2.2 ID Generators (`backend/core/ids.py`)

Updated [`backend/core/ids.py`](file:///c:/VyaparSetu/VyparSetu/paytm-vyaparsetu/backend/core/ids.py) with prefix generators:
- `generate_packaging_adjustment_id()` $\rightarrow$ `pkg_xxxxxx`
- `generate_extraction_audit_id()` $\rightarrow$ `aud_xxxxxx`

---

### 2.3 ORM Model Extensions (`backend/db/models.py`)

Updated [`backend/db/models.py`](file:///c:/VyaparSetu/VyparSetu/paytm-vyaparsetu/backend/db/models.py):

#### 1. Extended `Invoice` Table (`invoices`)
Added 11 columns for format metadata, GST breakdown, and payment prefill:
- `challan_type` (`Text`, nullable)
- `capture_medium` (`Text`, nullable)
- `challan_number` (`Text`, nullable)
- `distributor_gstin` (`Text`, nullable)
- `vehicle_number` (`Text`, nullable)
- `payment_handle_type` (`Text`, nullable)
- `payment_handle_value` (`Text`, nullable)
- `tax_cgst` (`Numeric(10,2)`, nullable)
- `tax_sgst` (`Numeric(10,2)`, nullable)
- `tax_igst` (`Numeric(10,2)`, nullable)
- `additional_charges` (`Numeric(10,2)`, default=0)

#### 2. Extended `InvoiceLineItem` Table (`invoice_line_items`)
Added line-item audit columns and updated quantity type:
- `quantity` updated from `Integer` to `Numeric(10,2)` (supporting float quantities like kg/crates).
- `raw_text` (`Text`, nullable)
- `unit` (`Text`, nullable)
- `hsn_code` (`Text`, nullable)
- `is_free_scheme` (`Boolean`, default=False)

#### 3. Created `InvoicePackagingAdjustment` Table (`invoice_packaging_adjustments`)
Tracks returnable crates and packaging deposits:
- `adjustment_id` (`Text`, Primary Key, `pkg_xxxxxx`)
- `invoice_id` (`Text`, Foreign Key $\rightarrow$ `invoices.invoice_id`)
- `item_name` (`Text`, Not Null)
- `direction` (`Text`, Not Null, `RECEIVED` / `RETURNED`)
- `quantity` (`Integer`, Not Null)

#### 4. Created `InvoiceExtractionAudit` Table (`invoice_extraction_audit`)
Stores audit trails and model performance data:
- `audit_id` (`Text`, Primary Key, `aud_xxxxxx`)
- `invoice_id` (`Text`, Foreign Key $\rightarrow$ `invoices.invoice_id`)
- `ocr_raw_text` (`Text`, Nullable)
- `vision_llm_raw_response` (`JSONB`, Not Null)
- `model_used` (`Text`, Not Null)
- `escalated` (`Boolean`, Default=False)
- `merchant_edited_fields` (`ARRAY(Text)`, Nullable)
- `created_at` (`DateTime(timezone=True)`, Server Default `now()`)

---

### 2.4 Alembic Migration Revision

Generated and applied Alembic migration revision:
- **Revision File**: `backend/db/migrations/versions/2b3b75111a5a_extend_challan_schema_packaging_.py`
- **Execution Command**: `alembic upgrade head`

---

## 3. How to Test & Verify

### Method A: Database Schema Inspection (`psql` via Docker)

Open `psql` inside your running PostgreSQL container:

```powershell
docker exec -it vyaparsetu_postgres psql -U vyapar_user -d vyaparsetu_db
```

#### Query 1: Verify `invoices` Table Columns
```sql
\d invoices
```
*Expected Output: Confirms columns `challan_type`, `capture_medium`, `challan_number`, `distributor_gstin`, `vehicle_number`, `payment_handle_type`, `payment_handle_value`, `tax_cgst`, `tax_sgst`, `tax_igst`, `additional_charges` exist.*

#### Query 2: Verify `invoice_line_items` Table Columns
```sql
\d invoice_line_items
```
*Expected Output: Confirms `quantity` is `numeric(10,2)` and columns `raw_text`, `unit`, `hsn_code`, `is_free_scheme` exist.*

#### Query 3: Verify `invoice_packaging_adjustments` Table
```sql
\d invoice_packaging_adjustments
```
*Expected Output: Confirms `adjustment_id`, `invoice_id`, `item_name`, `direction`, `quantity` exist with Foreign Key to `invoices`.*

#### Query 4: Verify `invoice_extraction_audit` Table
```sql
\d invoice_extraction_audit
```
*Expected Output: Confirms `audit_id`, `invoice_id`, `ocr_raw_text`, `vision_llm_raw_response` (JSONB), `model_used`, `escalated`, `merchant_edited_fields` exist.*

---

### Method B: Automated Pytest Suite Execution

Run the complete backend unit test suite to verify 100% zero regressions:

```powershell
# 1. Navigate to backend folder
cd paytm-vyaparsetu/backend

# 2. Activate Virtual Environment
..\venv\Scripts\Activate.ps1

# 3. Run Pytest
python -m pytest -v
```

*Expected Result:*
```text
======================== 25 passed in ~2.81s ========================
```

---

### Method C: Pydantic Schema Verification Script

You can verify Pydantic Stage A–D schema validation by running:

```powershell
cd paytm-vyaparsetu/backend
python -c "
from vision.schemas import ChallanExtractionResult, LineItem, TaxBreakdown
res = ChallanExtractionResult(
    challan_type='FORMAL_GST',
    capture_medium='CAMERA_PHOTO',
    distributor_name_raw='Amul India Dairy',
    line_items=[LineItem(raw_text='Dahi 200g', canonical_item_name='Dahi 200g Pouch', quantity=50, unit='pouches', unit_rate=28.5, line_total=1425.0, item_confidence=0.92)],
    subtotal=1425.0,
    tax=TaxBreakdown(cgst=35.6, sgst=35.6),
    total_payable=1496.2,
    metadata_confidence=0.95,
    line_items_confidence=0.92,
    overall_confidence=0.93
)
print('Validated Schema Successfully:', res.challan_type, 'Total:', res.total_payable)
"
```

*Expected Output:*
```text
Validated Schema Successfully: FORMAL_GST Total: 1496.2
```

---

## 4. Git Delivery Summary

All changes have been committed and pushed to the main repository:
- **Commit Hash**: `83abe0e`
- **Commit Message**: `"Challan plan updated , models implemented"`
- **Files Modified/Created**: 17 files (+1,025 lines inserted).
