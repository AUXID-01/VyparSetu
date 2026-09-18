import io
import pytest
from PIL import Image, ExifTags
from vision.preprocessor import preprocess_challan_image
from vision.schemas import ChallanExtractionResult, LineItem, TaxBreakdown

def test_preprocess_challan_image_resize_and_grayscale():
    # Create a dummy large image (2000x2000)
    img = Image.new('RGB', (2000, 2000), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    color_bytes, gray_bytes, meta = preprocess_challan_image(img_bytes)
    
    assert meta.original_dimensions == (2000, 2000)
    assert meta.resized_to[0] <= 1600 and meta.resized_to[1] <= 1600
    assert meta.grayscale_variant_created is True
    assert meta.contrast_enhanced is True

def test_preprocess_challan_image_exif_rotation():
    # Create a dummy image
    img = Image.new('RGB', (100, 200), color='white')
    
    # Try to set EXIF orientation (6 = rotate 270)
    exif = img.getexif()
    orientation_key = None
    for k, v in ExifTags.TAGS.items():
        if v == 'Orientation':
            orientation_key = k
            break
    
    if orientation_key:
        exif[orientation_key] = 6
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', exif=exif)
    img_bytes = img_byte_arr.getvalue()
    
    color_bytes, gray_bytes, meta = preprocess_challan_image(img_bytes)
    
    # Original was 100x200. After rotating 270 degrees, it should be 200x100
    assert meta.original_dimensions == (100, 200)
    assert meta.was_rotated is True
    assert meta.resized_to == (200, 100)

def test_challan_extraction_result_schema_validation():
    data = {
        "challan_type": "FORMAL_GST",
        "capture_medium": "CAMERA_PHOTO",
        "distributor_name_raw": "Amul India Dairy",
        "line_items": [
            {
                "raw_text": "Dahi 200g",
                "canonical_item_name": "Dahi 200g Pouch",
                "quantity": 50,
                "unit": "pouches",
                "unit_rate": 28.5,
                "line_total": 1425.0,
                "item_confidence": 0.92
            }
        ],
        "subtotal": 1425.0,
        "tax": {
            "cgst": 35.6,
            "sgst": 35.6
        },
        "total_payable": 1496.2,
        "metadata_confidence": 0.95,
        "line_items_confidence": 0.92,
        "overall_confidence": 0.93
    }
    
    result = ChallanExtractionResult(**data)
    
    assert result.challan_type == "FORMAL_GST"
    assert len(result.line_items) == 1
    assert result.line_items[0].canonical_item_name == "Dahi 200g Pouch"
    assert result.tax.cgst == 35.6
    assert result.total_payable == 1496.2
    
    # Test fallback validation (missing required field)
    with pytest.raises(ValueError):
        ChallanExtractionResult(
            challan_type="FORMAL_GST",
            # missing capture_medium
            distributor_name_raw="Test",
            subtotal=100.0,
            total_payable=100.0,
            metadata_confidence=0.9,
            line_items_confidence=0.9,
            overall_confidence=0.9
        )
