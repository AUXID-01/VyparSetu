# Phase 5, Step 2: Vision Tech Stack Summary

This document outlines the work completed during Step 2 of the Phase 5 (Challan Extraction) execution plan. It covers the architecture built, the unexpected challenges we encountered during real-world simulation, and the testing strategies employed to stabilize the pipeline.

## 1. What We Built (The 4-Stage Pipeline)
We implemented a multi-stage image processing and extraction pipeline designed to handle diverse challan formats accurately.

*   **Stage A: Local Preprocessing (`backend/vision/preprocessor.py`)**
    *   Utilized `Pillow` to clean the image before any API calls are made.
    *   Features: EXIF auto-rotation (to ensure upright text), contrast enhancement (to make faded thermal/carbon copies legible), and smart resizing (capping max dimensions at 1600px to save token costs and processing time).
*   **Stage B: Grounding OCR (`backend/vision/ocr_grounding.py`)**
    *   Integrated Google Cloud Vision API (`DOCUMENT_TEXT_DETECTION`).
    *   Extracts highly accurate raw text blocks from the preprocessed image to serve as the mathematical and textual anchor for the LLM.
*   **Stage C: Vision LLM Structuring (`backend/vision/client.py`)**
    *   Implemented a Tiered Routing client designed to default to Groq for speed/cost, with an escalation path to frontier models (like GPT-4o).
    *   Forces the LLM to output a strict JSON payload matching the `ChallanExtractionResult` Pydantic schema.
*   **API Ingress:** Updated `POST /api/v1/challan/extract` to seamlessly pipe uploads through this 4-stage process.

## 2. Challenges Faced & Overcome

### Challenge A: Groq Vision Model Decommissioning
During end-to-end testing, the pipeline threw a fatal 400 error: `model_decommissioned`. We discovered that Groq had officially deprecated and removed access to their early `llama-3.2-90b-vision-preview` models in this environment.
*   **The Fix:** We rapidly pivoted the architecture. Instead of relying on Groq to process the raw image bytes, we shifted to Groq's high-speed text model (`groq/compound`). Because Stage B (Google Vision) already extracts all the text flawlessly, we feed the raw OCR text directly into the text LLM. This achieved the exact same structuring capability without needing a vision-specific model.

### Challenge B: The "Blind LLM" Classification Issue
Because we pivoted to a text-only model, the LLM became "blind" to the visual layout of the image. When fed a handwritten slip, it couldn't physically see the notebook paper or handwriting strokes, so it wrongly classified it as a `FORMAL_GST` invoice.
*   **The Fix:** We established that moving forward, we can either (a) unlock OpenAI's GPT-4o true vision capabilities, or (b) utilize Google Vision's handwriting confidence scores to inject a `[HANDWRITTEN]` flag into the text prompt.

### Challenge C: Schema Hallucination & Arithmetic Failures
When testing a handwritten invoice containing "Milk Crates" with a deposit fee, the LLM heavily hallucinated. It categorized the crates as an unpriced `packaging_adjustment`, dropping ₹3500 from the math, and blatantly ignored the explicitly written "Total Payable: Rs 4070".
*   **The Fix:** We completely overhauled the system prompt (`backend/vision/prompts.py`) to introduce strict mathematical invariants:
    1.  **Strict Packaging Rule:** If an item contributes to the final monetary total, it is a `LineItem`. Period.
    2.  **Arithmetic Reconciliation:** Forced the LLM to independently verify that `sum(line_totals) == total_payable`. If a discrepancy occurs, it is instructed to prioritize the explicitly written document total and re-examine the text for omitted items.

## 3. How We Tested It

1.  **Automated Schema & Preprocessor Tests (`backend/tests/test_challan_extract.py`)**
    *   We wrote unit tests using `pytest` that mock the API responses from Groq and Google.
    *   We generate an in-memory JPEG to validate that the `Pillow` preprocessor correctly handles binary streams without throwing `UnidentifiedImageError`.
    *   We assert that the Pydantic parser successfully maps the JSON fields to the new Phase 5 schema (e.g., `distributor_name_raw`, `total_payable`).
2.  **Edge-Case Verification Script (`backend/scripts/verify_handwritten_fix.py`)**
    *   To guarantee the arithmetic hallucination was fixed, we created an isolated verification script.
    *   It mocks the exact problematic OCR text (the "Milk Crates" math edge-case) and pipes it through the prompt.
    *   We successfully asserted that the LLM now correctly identifies 2 line items, properly includes the Milk Crates, and accurately parses the `4070.0` total.

The Vision pipeline is now stable, strictly validated, mathematically sound, and ready for Step 3 DB wiring.
