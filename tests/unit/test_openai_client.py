"""Tests for OpenAI LLM client."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure openai module is available (mocked if not installed)
if "openai" not in sys.modules:
    sys.modules["openai"] = MagicMock()

from libs.llm.openai_client import OpenAIClient


def _make_openai_response(
    content: str = '{"result": "ok"}',
    model: str = "gpt-4o-2025-01-01",
    prompt_tokens: int = 50,
    completion_tokens: int = 100,
    finish_reason: str = "stop",
    response_id: str = "chatcmpl-test",
):
    choice = MagicMock()
    choice.message.content = content
    choice.finish_reason = finish_reason

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    response.model = model
    response.id = response_id
    return response


class TestOpenAIClient:
    def setup_method(self):
        self.client = OpenAIClient(api_key="sk-test-key")
        self.mock_create = AsyncMock()
        self.client._client.chat.completions.create = self.mock_create

    @pytest.mark.asyncio
    async def test_generate(self):
        self.mock_create.return_value = _make_openai_response(
            content="Hello from GPT!"
        )
        resp = await self.client.generate("Say hello")
        assert resp.content == "Hello from GPT!"
        assert resp.model == "gpt-4o-2025-01-01"
        assert resp.input_tokens == 50
        assert resp.output_tokens == 100
        assert resp.total_tokens == 150
        assert resp.metadata["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        self.mock_create.return_value = _make_openai_response()
        await self.client.generate("Hello", system="You are a helper")
        call_kwargs = self.mock_create.call_args[1]
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helper"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_structured_uses_json_mode(self):
        self.mock_create.return_value = _make_openai_response(
            content='{"ideas": [{"title": "test"}]}'
        )
        resp = await self.client.generate_structured("Generate ideas")
        assert resp.metadata["structured"] is True
        call_kwargs = self.mock_create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_structured_system_appends_json_instruction(self):
        self.mock_create.return_value = _make_openai_response()
        await self.client.generate_structured("test", system="Base system")
        call_kwargs = self.mock_create.call_args[1]
        system_msg = call_kwargs["messages"][0]["content"]
        assert "valid JSON" in system_msg
        assert "Base system" in system_msg

    @pytest.mark.asyncio
    async def test_generate_empty_content(self):
        resp_mock = _make_openai_response()
        resp_mock.choices[0].message.content = None
        self.mock_create.return_value = resp_mock
        resp = await self.client.generate("test")
        assert resp.content == ""

    @pytest.mark.asyncio
    async def test_generate_no_usage(self):
        resp_mock = _make_openai_response()
        resp_mock.usage = None
        self.mock_create.return_value = resp_mock
        resp = await self.client.generate("test")
        assert resp.input_tokens == 0
        assert resp.output_tokens == 0

    def test_provider_name(self):
        assert self.client.provider_name == "openai"

    def test_default_model(self):
        assert self.client._model == "gpt-4o"

    def test_custom_model(self):
        client = OpenAIClient(api_key="k", model="gpt-4o-mini")
        assert client._model == "gpt-4o-mini"

    def test_build_messages_no_system(self):
        msgs = OpenAIClient._build_messages("hello", None)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_build_messages_with_system(self):
        msgs = OpenAIClient._build_messages("hello", "sys")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
