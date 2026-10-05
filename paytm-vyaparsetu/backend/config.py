import sys
from pathlib import Path
from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
if not ENV_FILE.exists():
    ENV_FILE = BASE_DIR.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://vyapar_user:vyapar_pass@localhost:5432/vyaparsetu_db"
    
    # Always required keys (no default, fails fast if missing)
    SARVAM_API_KEY: str
    GROQ_API_KEY: str
    GOOGLE_VISION_API_KEY: str
    INTERNAL_TOKEN: str
    VOICE_CONFIRMATION_SECRET: str
    
    # Optional / Fallback keys (can be empty)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    @field_validator("SARVAM_API_KEY", "GROQ_API_KEY", "GOOGLE_VISION_API_KEY", "INTERNAL_TOKEN", "VOICE_CONFIRMATION_SECRET", mode="before")
    def check_not_empty(cls, v, info):
        if not v or not str(v).strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return str(v).strip()

    def get_vision_api_key(self) -> str:
        return self.GOOGLE_VISION_API_KEY or self.GEMINI_API_KEY

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

try:
    settings = Settings()
except ValidationError as e:
    missing_keys = []
    for err in e.errors():
        loc = err.get("loc", [])
        if loc:
            missing_keys.append(str(loc[0]))
    
    msg = f"Startup Error: The following required environment variables are missing or empty: {', '.join(set(missing_keys))}"
    print(f"\n❌ {msg}\n")
    sys.exit(1)
