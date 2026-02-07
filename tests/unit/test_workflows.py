"""Tests for workflow dataclasses and activity dataclasses."""

from apps.worker_ingest.activities import (
    FetchTrendingInput,
    FetchTrendingOutput,
    StoreSourcesInput,
    StoreSourcesOutput,
)
from apps.worker_ingest.workflows import TrendIngestInput, TrendIngestOutput


class TestWorkflowDataclasses:
    def test_trend_ingest_input(self):
        inp = TrendIngestInput(
            brand_id="brand-123",
            niches=["tech", "finance"],
            platforms=["tiktok"],
        )
        assert inp.brand_id == "brand-123"
        assert inp.limit_per_niche == 10

    def test_trend_ingest_output(self):
        out = TrendIngestOutput(
            fetched_count=5,
            stored_count=5,
            source_ids=["id1", "id2"],
        )
        assert out.fetched_count == 5
        assert len(out.source_ids) == 2


class TestActivityDataclasses:
    def test_fetch_trending_input(self):
        inp = FetchTrendingInput(
            brand_id="b1",
            niches=["tech"],
            platforms=["mock"],
            limit_per_niche=5,
        )
        assert inp.limit_per_niche == 5

    def test_fetch_trending_output(self):
        out = FetchTrendingOutput(items_count=3, items=[{"url": "a"}, {"url": "b"}, {"url": "c"}])
        assert out.items_count == 3
        assert len(out.items) == 3

    def test_store_sources_input(self):
        inp = StoreSourcesInput(items=[{"url": "x"}])
        assert len(inp.items) == 1

    def test_store_sources_output(self):
        out = StoreSourcesOutput(stored_count=2, source_ids=["id1", "id2"])
        assert out.stored_count == 2
