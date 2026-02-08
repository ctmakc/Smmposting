"""Tests for Phase 3 API schemas."""

import uuid

from apps.api.schemas.idea import IdeaResponse
from apps.api.schemas.script import ScriptResponse
from apps.api.schemas.workflow import TriggerPlanningRequest, TriggerScriptRequest
from libs.db.enums import IdeaStatus, QCStatus


class TestIdeaSchema:
    def test_idea_response_from_dict(self):
        data = {
            "id": uuid.uuid4(),
            "brand_id": uuid.uuid4(),
            "title": "Test Idea",
            "angle": "tutorial",
            "persona": "dev",
            "format": "listicle",
            "priority_score": 75.5,
            "risk_score": 20.0,
            "effort_score": 30.0,
            "pattern_id": None,
            "status": IdeaStatus.PLANNED,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
        }
        resp = IdeaResponse(**data)
        assert resp.title == "Test Idea"
        assert resp.status == IdeaStatus.PLANNED


class TestScriptSchema:
    def test_script_response_from_dict(self):
        data = {
            "id": uuid.uuid4(),
            "idea_id": uuid.uuid4(),
            "version": 1,
            "hook_variants": ["h1", "h2", "h3"],
            "script_sections": {"hook": "text", "body": "text"},
            "on_screen_text": {"0:00": "text"},
            "broll_list": ["clip1"],
            "qc_status": QCStatus.APPROVED,
            "qc_notes": None,
            "generation_meta": {"model": "mock"},
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
        }
        resp = ScriptResponse(**data)
        assert resp.version == 1
        assert resp.qc_status == QCStatus.APPROVED


class TestNewWorkflowSchemas:
    def test_trigger_planning(self):
        req = TriggerPlanningRequest(
            brand_id="b1", brand_name="Test", niches=["tech"]
        )
        assert req.locale == "en"
        assert req.num_ideas == 3

    def test_trigger_script(self):
        req = TriggerScriptRequest(idea_id="i1", title="Test")
        assert req.risk_threshold == 50
        assert req.format == "listicle"
