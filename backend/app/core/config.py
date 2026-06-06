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

    # Audio storage
    AUDIO_STORAGE_PATH: str = "./storage/audio"
    MAX_AUDIO_UPLOAD_MB: int = 20
    ALLOWED_AUDIO_MIME_TYPES: str = "audio/webm,audio/ogg,audio/mp4,audio/mpeg,audio/wav"

    @property
    def allowed_audio_mime_types_list(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_AUDIO_MIME_TYPES.split(",") if t.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Auth — OTP
    DEV_OTP_CODE: str = "123456"
    OTP_EXPIRE_MINUTES: int = 5
    SMS_PROVIDER: str = "mock"

    # AI provider selection.
    # Values: "mock" (default, no API key needed) | "openai" (production)
    # "openclaw" is deprecated — falls back to mock with a warning.
    AI_PROVIDER: str = "mock"

    # ── OpenAI provider ──────────────────────────────────────────────────────
    # Required only when AI_PROVIDER=openai.
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-5.4-nano"
    OPENAI_TIMEOUT_SECONDS: int = 120
    OPENAI_MAX_RETRIES: int = 2
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_CONTEXT_MAX_MESSAGES: int = 24

    # SOCKS5 proxy enforcement.
    # When OPENAI_REQUIRE_PROXY=true (default), OpenAI requests are blocked unless
    # OPENAI_PROXY_URL is set to a valid socks5:// or socks5h:// URL.
    OPENAI_REQUIRE_PROXY: bool = True
    OPENAI_PROXY_URL: str = ""
    # Optional SOCKS5 credentials. When both are set, the provider injects them
    # into the proxy URL as socks5://user:pass@host:port.
    # Special characters in the password are percent-encoded automatically.
    OPENAI_PROXY_USER: str = ""
    OPENAI_PROXY_PASS: str = ""

    # ── OpenClaw provider (DEPRECATED — no longer active) ────────────────────
    # These vars are kept so existing .env files with OPENCLAW_* do not cause
    # startup errors. No production code reads them; AI_PROVIDER=openclaw now
    # falls back to mock with a deprecation warning.
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
