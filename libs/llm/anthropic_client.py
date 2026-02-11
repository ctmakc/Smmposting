"""Anthropic LLM client — Claude with retry and structured output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from libs.llm.base import LLMClient, LLMResponse

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic

logger = structlog.get_logger()

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)


class AnthropicClient(LLMClient):
    """Production Anthropic client with retry, structured output, and token tracking."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        default_temperature: float = 0.7,
    ) -> None:
        from anthropic import AsyncAnthropic

        self._client: AsyncAnthropic = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._default_temperature = default_temperature

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @_RETRY_DECORATOR
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        logger.debug(
            "anthropic_generate",
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        kwargs: dict = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            metadata={
                "stop_reason": response.stop_reason,
                "response_id": response.id,
            },
        )

    @_RETRY_DECORATOR
    async def generate_structured(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        system_msg = (system or "") + "\n\nYou MUST respond with valid JSON only. No markdown."
        system_msg = system_msg.strip()

        logger.debug(
            "anthropic_generate_structured",
            model=self._model,
            temperature=temperature,
        )

        response = await self._client.messages.create(
            model=self._model,
            system=system_msg,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        # Try to extract JSON from potential markdown wrapping
        content = _extract_json(content)

        try:
            json.loads(content)
        except json.JSONDecodeError:
            logger.warning("anthropic_invalid_json", content=content[:200])

        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            metadata={
                "stop_reason": response.stop_reason,
                "response_id": response.id,
                "structured": True,
            },
        )


def _extract_json(text: str) -> str:
    """Strip markdown code fences if the model wraps JSON in them."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Remove first line (```json) and last line (```)
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(lines).strip()
    return stripped
