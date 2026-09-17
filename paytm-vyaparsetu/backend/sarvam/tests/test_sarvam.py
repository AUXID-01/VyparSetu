import pytest
import sarvam

def test_number_to_hindi_words_50():
    assert sarvam.number_to_hindi_words(50) == "pachas"

def test_number_to_hindi_words_60():
    assert sarvam.number_to_hindi_words(60) == "saath"

def test_number_to_hindi_words_240():
    assert sarvam.number_to_hindi_words(240) == "do sau chalis"

def test_number_to_hindi_words_300():
    assert sarvam.number_to_hindi_words(300) == "teen sau"

def test_number_to_hindi_words_1500():
    assert sarvam.number_to_hindi_words(1500) == "ek hazaar paanch sau"

def test_facade_exports():
    expected_exports = {"transcribe_audio", "synthesize_speech", "number_to_hindi_words"}
    actual_exports = set(sarvam.__all__)
    assert actual_exports == expected_exports
    for export in expected_exports:
        assert hasattr(sarvam, export)
