from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://vyapar_user:vyapar_pass@localhost:5432/vyaparsetu_db"
    SARVAM_API_KEY: str = ""
    INTERNAL_TOKEN: str = "vyapar_internal_secret_token_123"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    N8N_PAYMENT_LINK_WEBHOOK_URL: str = "http://localhost:5678/webhook/payment-link"
    N8N_VENDOR_PAYOUT_WEBHOOK_URL: str = "http://localhost:5678/webhook/vendor-payout"
    N8N_ALERT_DISPATCH_WEBHOOK_URL: str = "http://localhost:5678/webhook/alert-dispatch"
    N8N_ONBOARDING_WEBHOOK_URL: str = "http://localhost:5678/webhook/merchant-onboarding"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
