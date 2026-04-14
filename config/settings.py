from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    BASE_URL: str = "http://localhost:8000"
    HEADLESS_MODE: bool = False
    EXECUTION_MODE: Literal["LIVE", "DRY_RUN"] = "LIVE"
    LLM_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = "dummy"
    
    # Timeouts & Retries
    DEFAULT_TIMEOUT_MS: int = 5000
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0  # Multiplier for exponential backoff

    class Config:
        env_file = ".env"

settings = Settings()
