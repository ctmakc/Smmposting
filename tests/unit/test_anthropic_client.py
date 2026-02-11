"""Tests for Anthropic LLM client."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure anthropic module is available (mocked if not installed)
if "anthropic" not in sys.modules:
    sys.modules["anthropic"] = MagicMock()

from libs.llm.anthropic_client import AnthropicClient, _extract_json


def _make_anthropic_response(
    content: str = '{"result": "ok"}',
    model: str = "claude-sonnet-4-5-20250929",
    input_tokens: int = 40,
    output_tokens: int = 80,
    stop_reason: str = "end_turn",
    response_id: str = "msg_test",
):
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = content

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    response = MagicMock()
    response.content = [text_block]
    response.usage = usage
    response.model = model
    response.stop_reason = stop_reason
    response.id = response_id
    return response


class TestAnthropicClient:
    def setup_method(self):
        self.client = AnthropicClient(api_key="sk-ant-test")
        self.mock_create = AsyncMock()
        self.client._client.messages.create = self.mock_create

    @pytest.mark.asyncio
    async def test_generate(self):
        self.mock_create.return_value = _make_anthropic_response(
            content="Hello from Claude!"
        )
        resp = await self.client.generate("Say hello")
        assert resp.content == "Hello from Claude!"
        assert resp.model == "claude-sonnet-4-5-20250929"
        assert resp.input_tokens == 40
        assert resp.output_tokens == 80
        assert resp.total_tokens == 120
        assert resp.metadata["stop_reason"] == "end_turn"

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        self.mock_create.return_value = _make_anthropic_response()
        await self.client.generate("Hello", system="You are a helper")
        call_kwargs = self.mock_create.call_args[1]
        assert call_kwargs["system"] == "You are a helper"

    @pytest.mark.asyncio
    async def test_generate_without_system(self):
        self.mock_create.return_value = _make_anthropic_response()
        await self.client.generate("Hello")
        call_kwargs = self.mock_create.call_args[1]
        assert "system" not in call_kwargs

    @pytest.mark.asyncio
    async def test_generate_structured(self):
        self.mock_create.return_value = _make_anthropic_response(
            content='{"ideas": [{"title": "test"}]}'
        )
        resp = await self.client.generate_structured("Generate ideas")
        assert resp.metadata["structured"] is True

    @pytest.mark.asyncio
    async def test_generate_structured_system_appends_json_instruction(self):
        self.mock_create.return_value = _make_anthropic_response()
        await self.client.generate_structured("test", system="Base system")
        call_kwargs = self.mock_create.call_args[1]
        assert "valid JSON" in call_kwargs["system"]
        assert "Base system" in call_kwargs["system"]

    @pytest.mark.asyncio
    async def test_generate_structured_strips_markdown(self):
        wrapped = '```json\n{"ok": true}\n```'
        self.mock_create.return_value = _make_anthropic_response(content=wrapped)
        resp = await self.client.generate_structured("test")
        assert resp.content == '{"ok": true}'

    @pytest.mark.asyncio
    async def test_multiple_text_blocks(self):
        block1 = MagicMock()
        block1.type = "text"
        block1.text = "Hello "
        block2 = MagicMock()
        block2.type = "text"
        block2.text = "World"
        block3 = MagicMock()
        block3.type = "tool_use"  # should be skipped

        resp_mock = _make_anthropic_response()
        resp_mock.content = [block1, block2, block3]
        self.mock_create.return_value = resp_mock

        resp = await self.client.generate("test")
        assert resp.content == "Hello World"

    def test_provider_name(self):
        assert self.client.provider_name == "anthropic"

    def test_default_model(self):
        assert self.client._model == "claude-sonnet-4-5-20250929"

    def test_custom_model(self):
        client = AnthropicClient(api_key="k", model="claude-haiku-4-5-20251001")
        assert client._model == "claude-haiku-4-5-20251001"


class TestExtractJson:
    def test_plain_json(self):
        assert _extract_json('{"a": 1}') == '{"a": 1}'

    def test_json_with_code_fence(self):
        text = '```json\n{"a": 1}\n```'
        assert _extract_json(text) == '{"a": 1}'

    def test_json_with_plain_fence(self):
        text = '```\n{"a": 1}\n```'
        assert _extract_json(text) == '{"a": 1}'

    def test_multiline_json_with_fence(self):
        text = '```json\n{\n  "a": 1,\n  "b": 2\n}\n```'
        result = _extract_json(text)
        assert '"a": 1' in result
        assert '"b": 2' in result

    def test_no_closing_fence(self):
        text = '```json\n{"a": 1}'
        result = _extract_json(text)
        assert '{"a": 1}' in result

    def test_whitespace_handling(self):
        assert _extract_json('  {"a": 1}  ') == '{"a": 1}'

    def test_empty_string(self):
        assert _extract_json("") == ""
