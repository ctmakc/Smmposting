"""LLM client factory — creates the right client based on settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from libs.llm.mock import MockLLMClient

if TYPE_CHECKING:
    from libs.llm.base import LLMClient

logger = structlog.get_logger()

# Module-level singleton
_llm_client: LLMClient | None = None


def get_llm_client(
    *,
    provider: str | None = None,
    openai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    model: str | None = None,
) -> LLMClient:
    """Get or create the LLM client singleton.

    Reads from Settings if no explicit args are passed.
    Supports: "openai", "anthropic", "mock".
    """
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    # Read from config if not passed explicitly
    if provider is None:
        from libs.core.config import get_settings

        settings = get_settings()
        provider = settings.llm_provider
        openai_api_key = openai_api_key or settings.openai_api_key
        anthropic_api_key = anthropic_api_key or settings.anthropic_api_key

    provider = provider.lower()

    if provider == "openai":
        if not openai_api_key:
            logger.warning("openai_api_key_missing, falling back to mock")
            _llm_client = MockLLMClient()
        else:
            from libs.llm.openai_client import OpenAIClient

            kwargs: dict = {"api_key": openai_api_key}
            if model:
                kwargs["model"] = model
            _llm_client = OpenAIClient(**kwargs)

    elif provider == "anthropic":
        if not anthropic_api_key:
            logger.warning("anthropic_api_key_missing, falling back to mock")
            _llm_client = MockLLMClient()
        else:
            from libs.llm.anthropic_client import AnthropicClient

            kwargs = {"api_key": anthropic_api_key}
            if model:
                kwargs["model"] = model
            _llm_client = AnthropicClient(**kwargs)

    elif provider == "mock":
        _llm_client = MockLLMClient()

    else:
        logger.error("unknown_llm_provider", provider=provider)
        raise ValueError(f"Unknown LLM provider: {provider}")

    logger.info("llm_client_created", provider=_llm_client.provider_name)
    return _llm_client


def reset_llm_client() -> None:
    """Reset the singleton (for testing)."""
    global _llm_client
    _llm_client = None
