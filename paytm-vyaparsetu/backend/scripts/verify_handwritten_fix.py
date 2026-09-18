import asyncio
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.client import extract_challan_pipeline
from vision.schemas import ChallanExtractionResult

MOCK_OCR_TEXT = """
1. Milk Crates : 10 units @ Rs 350 = Rs 3500
2. Dahi Pouch (200g) : 20 units @ Rs 28.50 = Rs 570
Total Payable: Rs 4070
UPI: Amelds shibutor@icicia
"""

MOCK_GROQ_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": """{
  "challan_type": "HANDWRITTEN_SCRAP",
  "challan_number": null,
  "challan_date": null,
  "distributor_name_raw": "Unknown",
  "distributor_gstin": null,
  "vehicle_number": null,
  "e_way_bill_number": null,
  "line_items": [
    {
      "raw_text": "1. Milk Crates : 10 units @ Rs 350 = Rs 3500",
      "canonical_item_name": "Milk Crates",
      "quantity": 10.0,
      "unit": "units",
      "unit_rate": 350.0,
      "line_total": 3500.0,
      "hsn_code": null,
      "is_free_scheme": false,
      "item_confidence": 0.9
    },
    {
      "raw_text": "2. Dahi Pouch (200g) : 20 units @ Rs 28.50 = Rs 570",
      "canonical_item_name": "Dahi Pouch 200g",
      "quantity": 20.0,
      "unit": "units",
      "unit_rate": 28.5,
      "line_total": 570.0,
      "hsn_code": null,
      "is_free_scheme": false,
      "item_confidence": 0.95
    }
  ],
  "packaging_adjustments": [],
  "payment_handle": {
    "handle_type": "UPI",
    "value": "amuldistributor@icici"
  },
  "subtotal": 4070.0,
  "tax": {
    "cgst": null,
    "sgst": null,
    "igst": null,
    "cess": null
  },
  "additional_charges": 0.0,
  "total_payable": 4070.0,
  "metadata_confidence": 0.85,
  "line_items_confidence": 0.9,
  "overall_confidence": 0.88
}"""
            }
        }
    ]
}

@patch('vision.client.preprocess_challan_image')
@patch('vision.client.get_ocr_grounding')
@patch('vision.client.httpx.post')
def verify_handwritten_fix(mock_post, mock_ocr, mock_preprocess):
    # Setup Mocks
    mock_preprocess.return_value = (b"color_bytes", b"gray_bytes", MagicMock())
    
    mock_ocr_result = MagicMock()
    mock_ocr_result.full_text = MOCK_OCR_TEXT
    mock_ocr.return_value = mock_ocr_result
    
    mock_httpx_response = MagicMock()
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = MOCK_GROQ_RESPONSE
    mock_post.return_value = mock_httpx_response

    print("Running extract_challan_pipeline with simulated handwritten OCR text...")
    
    # Run pipeline
    result, ocr_text, raw_resp, model, escalated = extract_challan_pipeline(
        image_bytes=b"dummy_image_data",
        capture_medium="CAMERA_PHOTO",
        request_id="test_handwritten_001"
    )

    print("\n--- Pipeline Results ---")
    print(f"Challan Type: {result.challan_type}")
    print(f"Line Items Count: {len(result.line_items)}")
    print(f"Total Payable: {result.total_payable}")
    print(f"UPI Handle Normalized: {result.payment_handle.value if result.payment_handle else None}")
    
    # Assertions
    assert result.challan_type == "HANDWRITTEN_SCRAP", f"Expected HANDWRITTEN_SCRAP, got {result.challan_type}"
    assert len(result.line_items) == 2, f"Expected 2 line items, got {len(result.line_items)}"
    assert result.total_payable == 4070.0, f"Expected 4070.0, got {result.total_payable}"
    assert result.payment_handle and result.payment_handle.value == "amuldistributor@icici", "UPI Handle was not normalized correctly"
    
    # Check that Milk Crates are actually in line items
    item_names = [item.canonical_item_name for item in result.line_items]
    assert "Milk Crates" in item_names, "Milk Crates was excluded from line_items!"

    print("\n✅ Verification Successful: All handwritten edge case asserts passed!")

if __name__ == "__main__":
    verify_handwritten_fix()
