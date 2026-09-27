"""
Application configuration, loaded from environment variables / .env file.
Keeping all config in one typed object avoids scattered os.getenv() calls
and makes missing/invalid config fail fast at startup instead of at request time.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    ENVIRONMENT: str = "development"  # "development" | "production"
    APP_NAME: str = "Likitha Portfolio API"

    # CORS — comma-separated list of allowed origins in production
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    # Where contact-form messages get delivered
    CONTACT_RECEIVER_EMAIL: str = ""

    # Resend (preferred — HTTPS API, works on hosts that block SMTP, e.g. Railway Hobby)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "Portfolio <onboarding@resend.dev>"

    # SMTP (fallback — local dev or hosts that allow outbound SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # Rate limiting
    CONTACT_RATE_LIMIT: str = "5/hour"  # per-IP limit on the contact endpoint

    # Storage
    # On Vercel only /tmp is writable (and it is temporary), so default there.
    DATABASE_PATH: str = "/tmp/submissions.db" if os.environ.get("VERCEL") else "data/submissions.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def email_transport(self) -> str | None:
        """Which email transport to use: "resend", "smtp", or None if unconfigured."""
        if not self.CONTACT_RECEIVER_EMAIL:
            return None
        if self.RESEND_API_KEY:
            return "resend"
        if self.SMTP_USERNAME and self.SMTP_PASSWORD:
            return "smtp"
        return None

    @property
    def email_enabled(self) -> bool:
        return self.email_transport is not None


@lru_cache
def get_settings() -> Settings:
    # Cached so we parse the environment once per process, not once per request.
    return Settings()
