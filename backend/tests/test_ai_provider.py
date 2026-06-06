"""
Smoke tests for the AI provider factory and OpenAIProvider proxy enforcement.
No real network calls are made in any test here.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _fake_settings(**overrides) -> MagicMock:
    s = MagicMock()
    s.AI_PROVIDER = "mock"
    s.OPENAI_API_KEY = ""
    s.OPENAI_BASE_URL = "https://api.openai.com/v1"
    s.OPENAI_MODEL = "gpt-5.4-nano"
    s.OPENAI_TIMEOUT_SECONDS = 30
    s.OPENAI_MAX_RETRIES = 1
    s.OPENAI_TEMPERATURE = 0.3
    s.OPENAI_MAX_TOKENS = 512
    s.OPENAI_REQUIRE_PROXY = True
    s.OPENAI_PROXY_URL = ""
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


# ---------------------------------------------------------------------------
# Provider factory tests
# ---------------------------------------------------------------------------

class TestProviderFactory:
    """Tests for get_ai_provider() routing logic."""

    def test_returns_mock_when_ai_provider_is_mock(self, monkeypatch):
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.mock_ai_provider import MockAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(AI_PROVIDER="mock"))
        assert isinstance(get_ai_provider(), MockAIProvider)

    def test_returns_mock_when_ai_provider_is_empty(self, monkeypatch):
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.mock_ai_provider import MockAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(AI_PROVIDER=""))
        assert isinstance(get_ai_provider(), MockAIProvider)

    def test_openclaw_deprecated_falls_back_to_mock(self, monkeypatch):
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.mock_ai_provider import MockAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(AI_PROVIDER="openclaw"))
        assert isinstance(get_ai_provider(), MockAIProvider)

    def test_openai_no_api_key_falls_back_to_mock(self, monkeypatch):
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.mock_ai_provider import MockAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(
            AI_PROVIDER="openai",
            OPENAI_API_KEY="",
            OPENAI_REQUIRE_PROXY=True,
            OPENAI_PROXY_URL="socks5://127.0.0.1:1080",
        ))
        assert isinstance(get_ai_provider(), MockAIProvider)

    def test_openai_no_proxy_url_falls_back_to_mock(self, monkeypatch):
        """OPENAI_REQUIRE_PROXY=true with empty proxy URL must not call OpenAI directly."""
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.mock_ai_provider import MockAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(
            AI_PROVIDER="openai",
            OPENAI_API_KEY="sk-test",
            OPENAI_REQUIRE_PROXY=True,
            OPENAI_PROXY_URL="",
        ))
        assert isinstance(get_ai_provider(), MockAIProvider)

    def test_openai_invalid_proxy_scheme_falls_back_to_mock(self, monkeypatch):
        """Non-SOCKS5 proxy scheme must be rejected — no HTTP proxy allowed."""
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.mock_ai_provider import MockAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(
            AI_PROVIDER="openai",
            OPENAI_API_KEY="sk-test",
            OPENAI_REQUIRE_PROXY=True,
            OPENAI_PROXY_URL="http://127.0.0.1:8080",
        ))
        assert isinstance(get_ai_provider(), MockAIProvider)

    def test_openai_with_socks5_proxy_creates_openai_provider(self, monkeypatch):
        """Valid SOCKS5 config produces an OpenAIProvider, not mock."""
        import app.core.config as cfg
        from app.services.ai_provider import get_ai_provider
        from app.services.openai_provider import OpenAIProvider

        monkeypatch.setattr(cfg, "settings", _fake_settings(
            AI_PROVIDER="openai",
            OPENAI_API_KEY="sk-test",
            OPENAI_REQUIRE_PROXY=True,
            OPENAI_PROXY_URL="socks5://127.0.0.1:1080",
        ))
        provider = get_ai_provider()
        assert isinstance(provider, OpenAIProvider)
        assert provider._proxy_url == "socks5://127.0.0.1:1080"


# ---------------------------------------------------------------------------
# OpenAIProvider construction tests (no network)
# ---------------------------------------------------------------------------

class TestOpenAIProviderInit:
    """Tests for OpenAIProvider.__init__ proxy enforcement (no network calls)."""

    def _make_settings(self, **overrides) -> MagicMock:
        base = dict(
            AI_PROVIDER="openai",
            OPENAI_API_KEY="sk-test",
            OPENAI_REQUIRE_PROXY=True,
            OPENAI_PROXY_URL="socks5://127.0.0.1:1080",
        )
        base.update(overrides)
        return _fake_settings(**base)

    def test_raises_when_proxy_required_and_url_empty(self):
        from app.services.ai_provider import AIProviderError
        from app.services.openai_provider import OpenAIProvider

        with pytest.raises(AIProviderError, match="OPENAI_PROXY_URL"):
            OpenAIProvider(self._make_settings(OPENAI_PROXY_URL=""))

    def test_raises_when_proxy_scheme_is_not_socks5(self):
        from app.services.ai_provider import AIProviderError
        from app.services.openai_provider import OpenAIProvider

        with pytest.raises(AIProviderError, match="socks5"):
            OpenAIProvider(self._make_settings(OPENAI_PROXY_URL="http://127.0.0.1:8080"))

    def test_accepts_socks5_scheme(self):
        from app.services.openai_provider import OpenAIProvider

        provider = OpenAIProvider(self._make_settings(OPENAI_PROXY_URL="socks5://127.0.0.1:1080"))
        assert provider._proxy_url == "socks5://127.0.0.1:1080"

    def test_accepts_socks5h_scheme(self):
        from app.services.openai_provider import OpenAIProvider

        provider = OpenAIProvider(self._make_settings(OPENAI_PROXY_URL="socks5h://127.0.0.1:1080"))
        assert provider._proxy_url == "socks5h://127.0.0.1:1080"

    def test_no_proxy_when_require_proxy_is_false(self):
        from app.services.openai_provider import OpenAIProvider

        provider = OpenAIProvider(self._make_settings(
            OPENAI_REQUIRE_PROXY=False,
            OPENAI_PROXY_URL="",
        ))
        assert provider._proxy_url is None

    def test_httpx_client_receives_proxy_kwarg(self, monkeypatch):
        """Verify httpx.Client is constructed with proxy= set to the SOCKS5 URL."""
        import httpx
        from app.services.openai_provider import OpenAIProvider

        captured_kwargs: list[dict] = []

        def mock_client_init(self_inner, **kwargs):
            captured_kwargs.append(dict(kwargs))
            raise RuntimeError("intercepted — no network call made")

        monkeypatch.setattr(httpx.Client, "__init__", mock_client_init)

        provider = OpenAIProvider(self._make_settings())
        with pytest.raises(RuntimeError, match="intercepted"):
            provider.generate_text([{"role": "user", "content": "ping"}])

        assert captured_kwargs, "httpx.Client was never constructed"
        assert captured_kwargs[0].get("proxy") == "socks5://127.0.0.1:1080"
