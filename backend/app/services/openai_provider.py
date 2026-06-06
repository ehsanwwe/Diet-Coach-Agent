"""
OpenAIProvider: Chat completions via OpenAI API, routed through a SOCKS5 proxy.

All config from OPENAI_* env vars only. If OPENAI_REQUIRE_PROXY=true and
OPENAI_PROXY_URL is absent or not a socks5:// / socks5h:// URL, this provider
raises AIProviderError at construction time — it never attempts a direct call.

SOCKS5 credentials (OPENAI_PROXY_USER / OPENAI_PROXY_PASS) are injected into
the proxy URL and percent-encoded. The password is never logged.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import httpx

from app.services.ai_provider import AIProvider, AIProviderError, AIProviderResult

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


def _inject_credentials(proxy_url: str, user: str, password: str) -> tuple[str, str]:
    """Return (authenticated_url, safe_url_for_logging).

    Percent-encodes both user and password so special characters (e.g. '/', '@', ':')
    are transmitted correctly by the SOCKS5 handshake.
    The safe URL replaces the password with *** for log output.
    If either credential is empty, the original URL is returned unchanged.
    """
    if not (user and password):
        return proxy_url, proxy_url

    parsed = urlsplit(proxy_url)
    encoded_user = quote(user, safe="")
    encoded_pass = quote(password, safe="")

    host = parsed.hostname or ""
    netloc_auth = f"{encoded_user}:{encoded_pass}@{host}"
    netloc_safe = f"{encoded_user}:***@{host}"
    if parsed.port:
        netloc_auth = f"{netloc_auth}:{parsed.port}"
        netloc_safe = f"{netloc_safe}:{parsed.port}"

    auth_url = urlunsplit((parsed.scheme, netloc_auth, parsed.path, parsed.query, parsed.fragment))
    safe_url = urlunsplit((parsed.scheme, netloc_safe, parsed.path, parsed.query, parsed.fragment))
    return auth_url, safe_url


class OpenAIProvider(AIProvider):
    def __init__(self, settings: Any) -> None:
        self._api_key = settings.OPENAI_API_KEY
        self._model = settings.OPENAI_MODEL
        self._timeout = float(settings.OPENAI_TIMEOUT_SECONDS)
        self._max_retries = int(settings.OPENAI_MAX_RETRIES)
        self._default_temperature = float(settings.OPENAI_TEMPERATURE)
        self._default_max_tokens = int(settings.OPENAI_MAX_TOKENS)

        base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self._url = f"{base_url}/chat/completions"

        require_proxy: bool = settings.OPENAI_REQUIRE_PROXY
        proxy_url: str = settings.OPENAI_PROXY_URL.strip()

        if require_proxy:
            if not proxy_url:
                raise AIProviderError(
                    "OPENAI_REQUIRE_PROXY=true but OPENAI_PROXY_URL is not configured. "
                    "Set a socks5:// proxy URL or switch to AI_PROVIDER=mock."
                )
            if not (proxy_url.startswith("socks5://") or proxy_url.startswith("socks5h://")):
                raise AIProviderError(
                    "OPENAI_REQUIRE_PROXY=true but OPENAI_PROXY_URL does not use a SOCKS5 "
                    f"scheme (got: {proxy_url.split('://')[0]}://...). "
                    "Only socks5:// or socks5h:// are accepted."
                )

        if proxy_url:
            user = settings.OPENAI_PROXY_USER.strip()
            password = settings.OPENAI_PROXY_PASS.strip()
            auth_url, safe_url = _inject_credentials(proxy_url, user, password)
            self._proxy_url: str | None = auth_url
            self._proxy_safe_url: str = safe_url
        else:
            self._proxy_url = None
            self._proxy_safe_url = ""

    def generate_text(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        temp = temperature if temperature is not None else self._default_temperature
        tokens = max_tokens if max_tokens is not None else self._default_max_tokens

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        client_kwargs: dict[str, Any] = {"timeout": self._timeout}
        if self._proxy_url:
            client_kwargs["proxy"] = self._proxy_url

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(**client_kwargs) as client:
                    response = client.post(self._url, headers=headers, json=payload)

                if response.status_code in _RETRYABLE_HTTP_STATUSES and attempt < self._max_retries:
                    logger.warning(
                        "OpenAI HTTP %d on attempt %d — retrying",
                        response.status_code,
                        attempt + 1,
                    )
                    last_error = httpx.HTTPStatusError(
                        message=f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    continue

                if response.status_code == 401:
                    raise AIProviderError("OpenAI authentication failed — check OPENAI_API_KEY")

                response.raise_for_status()
                data: dict[str, Any] = response.json()

                choices = data.get("choices") or []
                if not choices:
                    raise AIProviderError("OpenAI returned an empty choices list")

                message = choices[0].get("message") or {}
                content: str = message.get("content") or ""
                finish_reason: str | None = choices[0].get("finish_reason")

                return AIProviderResult(
                    content=content,
                    provider="openai",
                    model=data.get("model", self._model),
                    finish_reason=finish_reason,
                    raw_metadata={
                        "id": data.get("id"),
                        "usage": data.get("usage"),
                    },
                    is_mock=False,
                )

            except AIProviderError:
                raise

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                logger.warning("OpenAI network error on attempt %d", attempt + 1)
                if attempt == self._max_retries:
                    break

            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning(
                    "OpenAI HTTP %d on attempt %d",
                    exc.response.status_code,
                    attempt + 1,
                )
                break

            except (KeyError, ValueError) as exc:
                last_error = exc
                logger.warning("OpenAI response parse error: %s", exc)
                break

        raise AIProviderError(f"OpenAI provider failed after retries: {last_error}")
