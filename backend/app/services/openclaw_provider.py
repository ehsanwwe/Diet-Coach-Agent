"""
OpenClawProvider: OpenAI-compatible chat completions via httpx.

All config from OPENCLAW_* env vars only. Retries on transient errors.
Falls back to a controlled AIProviderError on terminal failure — callers
decide whether to fall back to mock.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.ai_provider import AIProvider, AIProviderError, AIProviderResult

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


class OpenClawProvider(AIProvider):
    def __init__(self, settings: Any) -> None:
        self._base_url = settings.OPENCLAW_BASE_URL.rstrip("/")
        self._api_key = settings.OPENCLAW_API_KEY
        self._model = settings.OPENCLAW_MODEL
        self._path = settings.OPENCLAW_CHAT_COMPLETIONS_PATH
        self._timeout = float(settings.OPENCLAW_TIMEOUT_SECONDS)
        self._max_retries = int(settings.OPENCLAW_MAX_RETRIES)
        self._default_temperature = float(settings.OPENCLAW_TEMPERATURE)
        self._default_max_tokens = int(settings.OPENCLAW_MAX_TOKENS)

    def generate_text(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        temp = temperature if temperature is not None else self._default_temperature
        tokens = max_tokens if max_tokens is not None else self._default_max_tokens

        url = f"{self._base_url}{self._path}"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, headers=headers, json=payload)

                if response.status_code in _RETRYABLE_HTTP_STATUSES and attempt < self._max_retries:
                    logger.warning(
                        "OpenClaw HTTP %d on attempt %d, retrying",
                        response.status_code,
                        attempt + 1,
                    )
                    last_error = httpx.HTTPStatusError(
                        message=f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    continue

                response.raise_for_status()
                data = response.json()

                choices = data.get("choices") or []
                if not choices:
                    raise AIProviderError("Provider returned no choices")

                message = choices[0].get("message") or {}
                content: str = message.get("content") or ""
                finish_reason: str | None = choices[0].get("finish_reason")

                return AIProviderResult(
                    content=content,
                    provider="openclaw",
                    model=data.get("model", self._model),
                    finish_reason=finish_reason,
                    raw_metadata={
                        "id": data.get("id"),
                        "usage": data.get("usage"),
                    },
                    is_mock=False,
                )

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                logger.warning(
                    "OpenClaw network error on attempt %d: %s", attempt + 1, exc
                )
                if attempt == self._max_retries:
                    break

            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning(
                    "OpenClaw HTTP error on attempt %d: %s", attempt + 1, exc
                )
                break

            except (KeyError, ValueError) as exc:
                last_error = exc
                logger.warning("OpenClaw response parse error: %s", exc)
                break

        raise AIProviderError(f"OpenClaw provider failed after retries: {last_error}")
