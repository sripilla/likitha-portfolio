"""
Application configuration, loaded from environment variables / .env file.
Keeping all config in one typed object avoids scattered os.getenv() calls
and makes missing/invalid config fail fast at startup instead of at request time.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    ENVIRONMENT: str = "development"  # "development" | "production"
    APP_NAME: str = "Likitha Portfolio API"

    # CORS — comma-separated list of allowed origins in production
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    # SMTP (used to email contact-form submissions to Likitha)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    CONTACT_RECEIVER_EMAIL: str = ""  # where contact form messages get sent

    # Rate limiting
    CONTACT_RATE_LIMIT: str = "5/hour"  # per-IP limit on the contact endpoint

    # Storage
    DATABASE_PATH: str = "data/submissions.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def email_enabled(self) -> bool:
        return bool(self.SMTP_USERNAME and self.SMTP_PASSWORD and self.CONTACT_RECEIVER_EMAIL)


@lru_cache
def get_settings() -> Settings:
    # Cached so we parse the environment once per process, not once per request.
    return Settings()
