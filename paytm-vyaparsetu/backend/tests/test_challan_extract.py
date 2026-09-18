from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from config import settings
import io
from PIL import Image

client = TestClient(app)

MOCK_GROQ_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": """{
  "challan_type": "FORMAL_GST",
  "challan_number": "INV-10023",
  "challan_date": "2024-05-12",
  "distributor_name_raw": "Amul Distributor - Sector 4",
  "distributor_gstin": "07AABCB1234F1Z5",
  "vehicle_number": "DL1GC1234",
  "e_way_bill_number": null,
  "line_items": [
    {
      "raw_text": "Dahi 200g pouch x 50",
      "canonical_item_name": "Dahi 200g Pouch",
      "quantity": 50.0,
      "unit": "pouches",
      "unit_rate": 28.50,
      "line_total": 1425.00,
      "hsn_code": "0403",
      "is_free_scheme": false,
      "item_confidence": 0.95
    }
  ],
  "packaging_adjustments": [],
  "payment_handle": null,
  "subtotal": 1425.00,
  "tax": {
    "cgst": 35.60,
    "sgst": 35.60,
    "igst": null,
    "cess": null
  },
  "additional_charges": 0.0,
  "total_payable": 1496.20,
  "metadata_confidence": 0.95,
  "line_items_confidence": 0.92,
  "overall_confidence": 0.93
}"""
            }
        }
    ]
}

@patch("vision.client.httpx.post")
def test_challan_extract_endpoint_success(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "mock_groq_key_123")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_GROQ_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Generate a valid tiny JPEG image to pass PIL's UnidentifiedImageError check
    img = Image.new('RGB', (10, 10), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    sample_image_content = img_byte_arr.getvalue()
    
    response = client.post(
        "/api/v1/challan/extract",
        data={"merchant_id": "mer_test_01"},
        files={"image": ("challan_sample.jpg", sample_image_content, "image/jpeg")}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    
    # Assert on new schema fields
    assert data["challan_type"] == "FORMAL_GST"
    assert "distributor_name_raw" in data
    assert "line_items" in data
    assert len(data["line_items"]) > 0
    assert data["line_items"][0]["canonical_item_name"] == "Dahi 200g Pouch"
    assert data["total_payable"] > 0
    assert data["overall_confidence"] > 0
    assert data["capture_medium"] == "CAMERA_PHOTO"

def test_challan_extract_endpoint_empty_file():
    empty_content = b"tiny"
    response = client.post(
        "/api/v1/challan/extract",
        data={"merchant_id": "mer_test_01"},
        files={"image": ("empty.jpg", empty_content, "image/jpeg")}
    )

    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "LOW_CONFIDENCE_EXTRACTION"
