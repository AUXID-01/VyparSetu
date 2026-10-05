import pytest
import sarvam

@pytest.mark.parametrize("input_value, expected_text", [
    (100, "100"),
    (1000, "1000"),
    (100000, "1,00,000"),
    (150.50, "150.50"),
    (1234567.89, "12,34,567.89"),
    (0.50, "0.50"),
    (0, "0")
])
def test_format_inr_text_passthrough(input_value, expected_text):
    """
    Tests that numeric amounts are correctly formatted into raw text
    with proper Indian commas and decimals for TTS passthrough.
    """
    assert sarvam.format_inr_text(input_value) == expected_text

def test_facade_exports():
    expected_exports = {"transcribe_audio", "synthesize_speech", "format_inr_text"}
    actual_exports = set(sarvam.__all__)
    assert actual_exports == expected_exports
    for export in expected_exports:
        assert hasattr(sarvam, export)
