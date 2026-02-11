"""Tests for LLM client factory."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure optional deps are mockable
if "openai" not in sys.modules:
    sys.modules["openai"] = MagicMock()
if "anthropic" not in sys.modules:
    sys.modules["anthropic"] = MagicMock()

from libs.llm.factory import get_llm_client, reset_llm_client
from libs.llm.mock import MockLLMClient


@pytest.fixture(autouse=True)
def _reset():
    reset_llm_client()
    yield
    reset_llm_client()


class TestGetLLMClient:
    def test_mock_provider(self):
        client = get_llm_client(provider="mock")
        assert isinstance(client, MockLLMClient)
        assert client.provider_name == "mock"

    def test_singleton_returns_same_instance(self):
        c1 = get_llm_client(provider="mock")
        c2 = get_llm_client(provider="mock")
        assert c1 is c2

    def test_reset_clears_singleton(self):
        c1 = get_llm_client(provider="mock")
        reset_llm_client()
        c2 = get_llm_client(provider="mock")
        assert c1 is not c2

    def test_openai_without_key_falls_back_to_mock(self):
        client = get_llm_client(provider="openai", openai_api_key="")
        assert isinstance(client, MockLLMClient)

    def test_anthropic_without_key_falls_back_to_mock(self):
        client = get_llm_client(provider="anthropic", anthropic_api_key="")
        assert isinstance(client, MockLLMClient)

    def test_openai_with_key_creates_openai_client(self):
        client = get_llm_client(provider="openai", openai_api_key="sk-test-key")
        assert client.provider_name == "openai"

    def test_anthropic_with_key_creates_anthropic_client(self):
        client = get_llm_client(provider="anthropic", anthropic_api_key="sk-ant-test")
        assert client.provider_name == "anthropic"

    def test_openai_with_custom_model(self):
        client = get_llm_client(
            provider="openai", openai_api_key="sk-test", model="gpt-4o-mini"
        )
        assert client.provider_name == "openai"
        assert client._model == "gpt-4o-mini"

    def test_anthropic_with_custom_model(self):
        client = get_llm_client(
            provider="anthropic", anthropic_api_key="sk-ant-test", model="claude-haiku-4-5-20251001"
        )
        assert client.provider_name == "anthropic"
        assert client._model == "claude-haiku-4-5-20251001"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_client(provider="gemini")

    def test_reads_from_settings_when_no_args(self):
        with patch("libs.core.config.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "mock"
            mock_settings.return_value.openai_api_key = ""
            mock_settings.return_value.anthropic_api_key = ""
            client = get_llm_client()
            assert isinstance(client, MockLLMClient)
