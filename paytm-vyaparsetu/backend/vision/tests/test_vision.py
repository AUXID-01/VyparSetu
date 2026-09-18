import pytest
from unittest.mock import MagicMock, patch
from vision import extract_challan
from core.errors import AppException, ErrorCode
from config import settings

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
def test_extract_challan_structure(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_VISION_API_KEY", "mock_gemini_key_123")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_GEMINI_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    sample_image_bytes = b"fake_image_bytes_for_testing_challan_ocr_sample_longer_than_100_bytes_padding_padding_padding_padding_padding_padding_padding"
    result = extract_challan(sample_image_bytes, request_id="test_req_01")

    assert "distributor_name_guess" in result
    assert "line_items" in result
    assert "total_amount" in result
    assert "extraction_confidence" in result

    assert result["distributor_name_guess"] == "Amul Distributor - Sector 4"
    assert isinstance(result["line_items"], list)
    assert result["line_items"][0]["sku"] == "Dahi 200G Pouch"
    assert result["total_amount"] == 1425.00
    assert 0.0 <= result["extraction_confidence"] <= 1.0

@patch("vision.client.httpx.post")
def test_sku_normalization(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_VISION_API_KEY", "mock_gemini_key_123")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_GEMINI_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    sample_image_bytes = b"fake_image_bytes_for_testing_challan_ocr_sample_longer_than_100_bytes_padding_padding_padding_padding_padding_padding_padding"
    result = extract_challan(sample_image_bytes, request_id="test_req_02")

    for item in result["line_items"]:
        sku = item["sku"]
        assert sku == sku.strip()
        assert sku[0].isupper()

def test_empty_image_guard():
    empty_bytes = b"tiny"
    with pytest.raises(AppException) as exc_info:
        extract_challan(empty_bytes, request_id="test_req_03")
    assert exc_info.value.code == ErrorCode.LOW_CONFIDENCE_EXTRACTION

def test_missing_api_key_raises_app_exception(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_VISION_API_KEY", "")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    
    sample_bytes = b"fake_image_bytes_longer_than_100_bytes_padding_padding_padding_padding_padding_padding_padding_padding_padding_padding"
    with pytest.raises(AppException) as exc_info:
        extract_challan(sample_bytes, request_id="test_req_04")
    assert exc_info.value.code == ErrorCode.SARVAM_API_ERROR
    assert "GOOGLE_VISION_API_KEY" in exc_info.value.message
