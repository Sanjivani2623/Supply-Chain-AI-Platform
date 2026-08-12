"""
Centralized application configuration.
All values come from environment variables (.env) - never hard-code secrets.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    # Database (SQLite by default — a single local file, zero server setup)
    DATABASE_URL: str = "sqlite:///./data/scai.db"

    # Redis / Celery (optional — only needed if you run the background worker;
    # the API works standalone without it via the manual /ingest, /run-checks,
    # and forecast endpoints)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External data sources
    EVENT_REGISTRY_API_KEY: str = ""

    # LLM
    LLM_PROVIDER: str = "gemini"       # anthropic | gemini | openrouter
    LLM_MODEL: str = ""                # blank = provider-specific sensible default
    LLM_API_KEY: str = ""              # used when LLM_PROVIDER=anthropic
    GEMINI_API_KEY: str = ""           # used when LLM_PROVIDER=gemini (Google AI Studio key)
    OPENROUTER_API_KEY: str = ""       # used when LLM_PROVIDER=openrouter

    # Embeddings
    EMBEDDING_PROVIDER: str = "local"  # local | openai | anthropic
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_DIM: int = 384

    # Alerts
    SLACK_WEBHOOK_URL: str = ""
    EMAIL_API_KEY: str = ""
    EMAIL_FROM: str = "alerts@supplychain-ai.example.com"

    # Storage
    STORAGE_BUCKET: str = "./storage"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
