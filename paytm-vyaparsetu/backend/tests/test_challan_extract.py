from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from config import settings

client = TestClient(app)

MOCK_GEMINI_RESPONSE = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": """{
  "distributor_name_guess": "Amul Distributor - Sector 4",
  "line_items": [
    {
      "sku": "dahi 200g pouch",
      "quantity": 50,
      "unit_price": 28.50
    }
  ],
  "total_amount": 1425.00,
  "extraction_confidence": 0.88
}"""
                    }
                ]
            }
        }
    ]
}

@patch("vision.client.httpx.post")
def test_challan_extract_endpoint_success(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_VISION_API_KEY", "mock_gemini_key_123")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_GEMINI_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    sample_image_content = b"fake_image_bytes_for_testing_challan_ocr_sample_longer_than_100_bytes_padding_padding_padding_padding_padding_padding_padding"
    response = client.post(
        "/api/v1/challan/extract",
        data={"merchant_id": "mer_test_01"},
        files={"image": ("challan_sample.jpg", sample_image_content, "image/jpeg")}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "distributor_name_guess" in data
    assert "line_items" in data
    assert len(data["line_items"]) > 0
    assert data["total_amount"] > 0

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
