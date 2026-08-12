import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniBrain"
    VERSION: str = "0.1.0"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # OpenAI Key (इसे .env से रीड करने के लिए फ़ील्ड सेट किया है)
    OPENAI_API_KEY: str = Field(default="mock-key-for-test")

    
    API_KEY: str = Field(default="omnibrain-super-secret-api-key")
    API_KEY_NAME: str = "X-API-Key"
    
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-3.6-flash"
    # SQL Agent
    SQL_AGENT_MODEL: str = "gpt-4o"
    TEMPERATURE: float = 0.0
    # Qdrant DB Config
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    VECTOR_DB_COLLECTION: str = "omnibrain_vectors"
    SEARCH_SCORE_THRESHOLD: float = 0.75

    # SQL DB Config
    SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "stock_history.db")

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# यह वो 'settings' वेरिएबल है जिसे हम इम्पोर्ट कर रहे हैं
settings = Settings()