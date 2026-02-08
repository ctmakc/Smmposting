"""Tests for Phase 5 API schemas."""

import uuid

from apps.api.schemas.metrics import MetricsResponse, RunResponse
from apps.api.schemas.workflow import TriggerMetricsRequest
from libs.db.enums import MetricsWindow, RunStatus


class TestMetricsSchema:
    def test_metrics_response(self):
        data = {
            "id": uuid.uuid4(),
            "post_id": uuid.uuid4(),
            "window": MetricsWindow.H24,
            "views": 15000,
            "watch_time": 42.5,
            "retention": 55.0,
            "ctr": 6.2,
            "comments": 120,
            "shares": 45,
            "saves": 22,
            "sentiment": 0.7,
            "top_questions": ["How?", "What tools?"],
            "collected_at": "2025-02-01T12:00:00Z",
        }
        resp = MetricsResponse(**data)
        assert resp.window == MetricsWindow.H24
        assert resp.views == 15000
        assert len(resp.top_questions) == 2


class TestRunSchema:
    def test_run_response(self):
        data = {
            "id": uuid.uuid4(),
            "workflow_id": "metrics-abc-12345678",
            "trigger_type": "cron",
            "started_at": "2025-02-01T10:00:00Z",
            "finished_at": None,
            "status": RunStatus.RUNNING,
            "errors": None,
        }
        resp = RunResponse(**data)
        assert resp.status == RunStatus.RUNNING
        assert resp.finished_at is None

    def test_run_response_completed(self):
        data = {
            "id": uuid.uuid4(),
            "workflow_id": "ingest-xyz-87654321",
            "trigger_type": "manual",
            "started_at": "2025-02-01T10:00:00Z",
            "finished_at": "2025-02-01T10:05:00Z",
            "status": RunStatus.COMPLETED,
            "errors": None,
        }
        resp = RunResponse(**data)
        assert resp.status == RunStatus.COMPLETED
        assert resp.finished_at is not None

    def test_run_response_with_errors(self):
        data = {
            "id": uuid.uuid4(),
            "workflow_id": "publish-fail-00000000",
            "trigger_type": "cron",
            "started_at": "2025-02-01T10:00:00Z",
            "finished_at": "2025-02-01T10:01:00Z",
            "status": RunStatus.FAILED,
            "errors": {"message": "Platform API timeout"},
        }
        resp = RunResponse(**data)
        assert resp.status == RunStatus.FAILED
        assert resp.errors is not None
        assert "timeout" in resp.errors["message"]


class TestTriggerMetricsSchema:
    def test_trigger_metrics_defaults(self):
        req = TriggerMetricsRequest(
            post_id="p1",
            platform="tiktok",
            platform_post_url="https://tiktok.com/post/123",
            title="My Video",
            brand_id="b1",
            brand_name="TestBrand",
        )
        assert req.niches == []
        assert req.num_followup_ideas == 3

    def test_trigger_metrics_full(self):
        req = TriggerMetricsRequest(
            post_id="p1",
            platform="youtube",
            platform_post_url="https://youtube.com/watch?v=abc",
            title="AI Tools Review",
            brand_id="b1",
            brand_name="TechBrand",
            niches=["tech", "ai"],
            num_followup_ideas=5,
        )
        assert len(req.niches) == 2
        assert req.num_followup_ideas == 5
