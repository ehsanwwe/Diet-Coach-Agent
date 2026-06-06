"""
AIProvider abstract base class, result type, and provider factory.

Supported providers: "mock" (default), "openai".
"openclaw" is deprecated and routes to mock with a warning.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AIProviderResult:
    content: str
    provider: str
    model: str
    finish_reason: str | None = None
    raw_metadata: dict[str, Any] | None = None
    is_mock: bool = False


@dataclass
class AIToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AIToolCallResult:
    assistant_message: str
    tool_calls: list["AIToolCall"]
    provider: str
    model: str
    finish_reason: str | None = None
    is_mock: bool = False
    raw_tool_calls: list[dict[str, Any]] | None = None


class AIProvider(ABC):
    @abstractmethod
    def generate_text(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        ...

    @property
    def supports_tools(self) -> bool:
        return False

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> "AIToolCallResult":
        raise NotImplementedError("This provider does not support tool calling")


class AIProviderError(Exception):
    """Raised when an AI provider call fails unrecoverably."""


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider, falling back to mock on misconfiguration."""
    from app.core.config import settings
    from app.services.mock_ai_provider import MockAIProvider

    provider_name = settings.AI_PROVIDER.strip().lower()

    if provider_name == "openai":
        if not settings.OPENAI_API_KEY.strip():
            logger.error(
                "AI_PROVIDER=openai but OPENAI_API_KEY is not set — falling back to mock"
            )
            return MockAIProvider()
        try:
            from app.services.openai_provider import OpenAIProvider
            return OpenAIProvider(settings)
        except AIProviderError as exc:
            logger.error("OpenAI provider configuration error: %s — falling back to mock", exc)
            return MockAIProvider()
        except Exception as exc:
            logger.error("OpenAI provider init failed: %s — falling back to mock", exc)
            return MockAIProvider()

    if provider_name == "openclaw":
        logger.warning(
            "AI_PROVIDER=openclaw is deprecated and no longer active. "
            "Use AI_PROVIDER=openai or AI_PROVIDER=mock. Falling back to mock."
        )
        return MockAIProvider()

    return MockAIProvider()
