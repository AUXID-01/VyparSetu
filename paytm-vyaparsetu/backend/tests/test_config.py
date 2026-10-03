import pytest
from pydantic import ValidationError
import os
import sys

def reload_config():
    if "config" in sys.modules:
        del sys.modules["config"]
    import config
    return config

def test_settings_fails_on_missing_required_keys(monkeypatch):
    # Set them to empty so pydantic evaluates them as empty strings
    # overriding any local .env file.
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("GOOGLE_VISION_API_KEY", "")
    monkeypatch.setenv("INTERNAL_TOKEN", "")
    
    with pytest.raises(SystemExit) as exc_info:
        reload_config()
    
    assert exc_info.value.code == 1

def test_settings_fails_on_empty_required_keys(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "   ")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid")
    monkeypatch.setenv("GOOGLE_VISION_API_KEY", "valid")
    monkeypatch.setenv("INTERNAL_TOKEN", "valid")
    
    with pytest.raises(SystemExit) as exc_info:
        reload_config()
        
    assert exc_info.value.code == 1

def test_settings_succeeds_with_required_keys(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "valid_key")
    monkeypatch.setenv("GROQ_API_KEY", "valid_key")
    monkeypatch.setenv("GOOGLE_VISION_API_KEY", "valid_key")
    monkeypatch.setenv("INTERNAL_TOKEN", "valid_token")
    
    config = reload_config()
    assert config.settings.SARVAM_API_KEY == "valid_key"
    assert config.settings.GROQ_API_KEY == "valid_key"
