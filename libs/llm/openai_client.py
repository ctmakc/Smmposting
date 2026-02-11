"""OpenAI LLM client — GPT-4o / GPT-4o-mini with retry and structured output."""

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
    from openai import AsyncOpenAI

logger = structlog.get_logger()

# Retry on transient OpenAI errors
_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)


class OpenAIClient(LLMClient):
    """Production OpenAI client with retry, structured output, and token tracking."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        default_temperature: float = 0.7,
    ) -> None:
        from openai import AsyncOpenAI

        self._client: AsyncOpenAI = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._default_temperature = default_temperature

    @property
    def provider_name(self) -> str:
        return "openai"

    @_RETRY_DECORATOR
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        messages = self._build_messages(prompt, system)

        logger.debug(
            "openai_generate",
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            metadata={
                "finish_reason": choice.finish_reason,
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
        system_msg = (system or "") + "\n\nYou MUST respond with valid JSON only."
        messages = self._build_messages(prompt, system_msg.strip())

        logger.debug(
            "openai_generate_structured",
            model=self._model,
            temperature=temperature,
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        choice = response.choices[0]
        usage = response.usage
        content = choice.message.content or "{}"

        # Validate JSON
        try:
            json.loads(content)
        except json.JSONDecodeError:
            logger.warning("openai_invalid_json", content=content[:200])

        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            metadata={
                "finish_reason": choice.finish_reason,
                "response_id": response.id,
                "structured": True,
            },
        )

    @staticmethod
    def _build_messages(
        prompt: str, system: str | None
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages
