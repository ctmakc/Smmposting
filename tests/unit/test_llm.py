"""Tests for LLM abstraction and mock client."""

import json

import pytest

from libs.llm.base import LLMClient, LLMResponse
from libs.llm.mock import MockLLMClient


class TestLLMResponse:
    def test_total_tokens(self):
        r = LLMResponse(content="hi", model="test", input_tokens=10, output_tokens=20)
        assert r.total_tokens == 30

    def test_defaults(self):
        r = LLMResponse(content="x", model="m")
        assert r.total_tokens == 0
        assert r.metadata == {}


class TestMockLLMClient:
    def test_is_llm_client(self):
        assert isinstance(MockLLMClient(), LLMClient)

    def test_provider_name(self):
        assert MockLLMClient().provider_name == "mock"

    @pytest.mark.asyncio
    async def test_generate_gap_analysis(self):
        client = MockLLMClient()
        resp = await client.generate("Analyze the gap in tech content")
        data = json.loads(resp.content)
        assert "gaps" in data
        assert len(data["gaps"]) > 0
        assert data["gaps"][0]["opportunity_score"] > 0

    @pytest.mark.asyncio
    async def test_generate_ideas(self):
        client = MockLLMClient()
        resp = await client.generate_structured("Generate ideas for this brand")
        data = json.loads(resp.content)
        assert "ideas" in data
        assert len(data["ideas"]) == 3
        for idea in data["ideas"]:
            assert "title" in idea
            assert "trend_score" in idea

    @pytest.mark.asyncio
    async def test_generate_script(self):
        client = MockLLMClient()
        resp = await client.generate("Write a script for this video")
        data = json.loads(resp.content)
        assert "hook_variants" in data
        assert len(data["hook_variants"]) >= 3
        assert "script_sections" in data
        assert "hook" in data["script_sections"]
        assert "body" in data["script_sections"]

    @pytest.mark.asyncio
    async def test_generate_qc(self):
        client = MockLLMClient()
        resp = await client.generate("QC check this script")
        data = json.loads(resp.content)
        assert "approved" in data
        assert "score" in data
        assert isinstance(data["approved"], bool)

    @pytest.mark.asyncio
    async def test_token_counting(self):
        client = MockLLMClient()
        resp = await client.generate("Hello world test prompt")
        assert resp.input_tokens > 0
        assert resp.output_tokens > 0
        assert resp.model == "mock-v1"

    @pytest.mark.asyncio
    async def test_default_response(self):
        client = MockLLMClient()
        resp = await client.generate("something completely unrelated")
        data = json.loads(resp.content)
        assert "response" in data
