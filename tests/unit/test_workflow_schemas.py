"""Tests for workflow API schemas."""

from apps.api.schemas.workflow import (
    TriggerIngestRequest,
    TriggerIngestResponse,
    WorkflowStatusResponse,
)


class TestWorkflowSchemas:
    def test_trigger_ingest_request(self):
        req = TriggerIngestRequest(
            brand_id="brand-1",
            niches=["tech"],
            platforms=["tiktok", "youtube"],
        )
        assert req.brand_id == "brand-1"
        assert req.limit_per_niche == 10

    def test_trigger_ingest_request_custom_limit(self):
        req = TriggerIngestRequest(
            brand_id="b2",
            niches=["finance"],
            platforms=["mock"],
            limit_per_niche=5,
        )
        assert req.limit_per_niche == 5

    def test_trigger_ingest_response(self):
        resp = TriggerIngestResponse(
            workflow_id="ingest-123",
            run_id="run-456",
        )
        assert resp.status == "started"

    def test_workflow_status_response_no_result(self):
        resp = WorkflowStatusResponse(
            workflow_id="wf-1",
            run_id="run-1",
            status="RUNNING",
        )
        assert resp.result is None

    def test_workflow_status_response_with_result(self):
        resp = WorkflowStatusResponse(
            workflow_id="wf-1",
            run_id="run-1",
            status="COMPLETED",
            result={"fetched_count": 10, "stored_count": 10},
        )
        assert resp.result["fetched_count"] == 10
