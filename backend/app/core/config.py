"""
Application configuration loaded from environment variables.

Uses pydantic-settings BaseSettings so every config value is typed,
validated at startup, and sourced from environment or .env file.

BE-07: pydantic-settings BaseSettings
BE-12: SECRET_KEY validated at startup
"""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Diet Coach Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security (BE-12)
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "sqlite+pysqlite:///./app.db"

    # CORS
    # Comma-separated list; loaded from env, never hard-coded (BE-01)
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Auth — OTP
    DEV_OTP_CODE: str = "123456"
    OTP_EXPIRE_MINUTES: int = 5
    SMS_PROVIDER: str = "mock"

    # OpenClaw AI provider (all 10 vars: OC-02, INFRA-03)
    OPENCLAW_BASE_URL: str = ""
    OPENCLAW_API_KEY: str = ""
    OPENCLAW_MODEL: str = "gpt-4o"
    OPENCLAW_CHAT_COMPLETIONS_PATH: str = "/v1/chat/completions"
    OPENCLAW_TIMEOUT_SECONDS: int = 30
    OPENCLAW_MAX_RETRIES: int = 3
    OPENCLAW_TEMPERATURE: float = 0.7
    OPENCLAW_MAX_TOKENS: int = 1024
    OPENCLAW_CONTEXT_MAX_MESSAGES: int = 20
    OPENCLAW_CONTEXT_SUMMARY_ENABLED: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, value: str) -> str:
        """
        BE-12: Refuse startup if SECRET_KEY is absent or equals
        the placeholder value. This runs at import time via Settings().
        """
        placeholder = "changeme"
        cleaned_value = value.strip()
        if not cleaned_value or cleaned_value.lower() == placeholder:
            raise ValueError(
                "SECRET_KEY must be set in environment and must not be the "
                f'default placeholder "{placeholder}". '
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return value


# Module-level singleton. Import this everywhere.
# This call validates SECRET_KEY at import time (BE-12).
# In tests, patch settings or set SECRET_KEY env var before importing.
settings = Settings()
