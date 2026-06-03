"""
AIProvider abstract base class, result type, and provider factory.

All providers (mock, openclaw) implement the AIProvider interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIProviderResult:
    content: str
    provider: str
    model: str
    finish_reason: str | None = None
    raw_metadata: dict[str, Any] | None = None
    is_mock: bool = False


class AIProvider(ABC):
    @abstractmethod
    def generate_text(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        ...


class AIProviderError(Exception):
    """Raised when an AI provider call fails unrecoverably."""


def get_ai_provider() -> AIProvider:
    """Return the configured provider, falling back to mock if unconfigured or unavailable."""
    from app.core.config import settings
    from app.services.mock_ai_provider import MockAIProvider

    provider_name = settings.AI_PROVIDER.strip().lower()
    if provider_name == "openclaw" and settings.OPENCLAW_BASE_URL.strip():
        try:
            from app.services.openclaw_provider import OpenClawProvider
            return OpenClawProvider(settings)
        except Exception:
            return MockAIProvider()
    return MockAIProvider()
