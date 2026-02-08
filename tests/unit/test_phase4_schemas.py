"""Tests for Phase 4 API schemas."""

import uuid
from datetime import UTC, datetime

from apps.api.schemas.post import (
    ApproveScriptRequest,
    PostCreate,
    PostResponse,
    PostUpdate,
    RejectScriptRequest,
)
from apps.api.schemas.workflow import TriggerPublishRequest
from libs.db.enums import PublishStatus


class TestPostSchemas:
    def test_post_create(self):
        pc = PostCreate(
            brand_id=uuid.uuid4(),
            script_id=uuid.uuid4(),
            platform="tiktok",
            caption="Test post",
            hashtags=["#test"],
        )
        assert pc.platform == "tiktok"
        assert pc.scheduled_at is None

    def test_post_create_with_schedule(self):
        now = datetime.now(UTC)
        pc = PostCreate(
            brand_id=uuid.uuid4(),
            script_id=uuid.uuid4(),
            platform="youtube",
            scheduled_at=now,
        )
        assert pc.scheduled_at == now

    def test_post_update(self):
        pu = PostUpdate(caption="Updated caption")
        assert pu.hashtags is None  # not set

    def test_post_response(self):
        data = {
            "id": uuid.uuid4(),
            "brand_id": uuid.uuid4(),
            "script_id": uuid.uuid4(),
            "platform": "instagram",
            "scheduled_at": None,
            "published_at": None,
            "caption": "Hello",
            "hashtags": ["#reels"],
            "utm_params": {"source": "cf"},
            "publish_status": PublishStatus.DRAFT,
            "url": None,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
        }
        resp = PostResponse(**data)
        assert resp.platform == "instagram"
        assert resp.publish_status == PublishStatus.DRAFT


class TestApprovalSchemas:
    def test_approve_request(self):
        req = ApproveScriptRequest(notes="Looks good")
        assert req.notes == "Looks good"

    def test_approve_request_no_notes(self):
        req = ApproveScriptRequest()
        assert req.notes is None

    def test_reject_request(self):
        req = RejectScriptRequest(reason="Bad quality", notes="Fix the hook")
        assert req.reason == "Bad quality"

    def test_reject_request_no_notes(self):
        req = RejectScriptRequest(reason="Too risky")
        assert req.notes is None


class TestTriggerPublishSchema:
    def test_trigger_publish_defaults(self):
        req = TriggerPublishRequest(
            post_id="p1",
            script_id="s1",
            platform="tiktok",
        )
        assert req.risk_threshold == 50
        assert req.qc_status == "approved"
        assert req.hashtags == []

    def test_trigger_publish_full(self):
        req = TriggerPublishRequest(
            post_id="p1",
            script_id="s1",
            platform="youtube",
            caption="My video",
            risk_score=25.0,
            risk_threshold=60,
            qc_status="approved",
            script_text="Script content here",
            hashtags=["#tech"],
            forbidden_topics=["gambling"],
            competitor_mentions=["CompetitorX"],
        )
        assert req.forbidden_topics == ["gambling"]
        assert req.competitor_mentions == ["CompetitorX"]
