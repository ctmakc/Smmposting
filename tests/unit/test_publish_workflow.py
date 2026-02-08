"""Tests for the publish workflow and activities."""

from apps.worker_publish.activities import (
    SafetyCheckInput,
    SafetyCheckOutput,
)
from apps.worker_publish.workflows import PublishInput, PublishOutput, PublishWorkflow


class TestPublishDataclasses:
    def test_publish_input_defaults(self):
        inp = PublishInput(
            post_id="post-1",
            script_id="script-1",
            platform="tiktok",
            caption="Test",
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Safe content about productivity.",
        )
        assert inp.hashtags == []
        assert inp.asset_urls == {}
        assert inp.forbidden_topics == []

    def test_publish_output(self):
        out = PublishOutput(
            post_id="post-1",
            published=True,
            publish_status="published",
            url="https://tiktok.com/post/123",
        )
        assert out.published is True
        assert out.url is not None

    def test_publish_output_failed(self):
        out = PublishOutput(
            post_id="post-1",
            published=False,
            publish_status="failed",
            safety_violations=["Risk too high"],
        )
        assert out.published is False
        assert len(out.safety_violations) == 1


class TestSafetyCheckInputOutput:
    def test_safety_check_input(self):
        inp = SafetyCheckInput(
            post_id="p1",
            script_id="s1",
            risk_score=30.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Content here",
            forbidden_topics=["drugs"],
        )
        assert inp.forbidden_topics == ["drugs"]

    def test_safety_check_output(self):
        out = SafetyCheckOutput(passed=True)
        assert out.violations == []

        out2 = SafetyCheckOutput(passed=False, violations=["Issue 1"])
        assert len(out2.violations) == 1


class TestWorkflowDefinition:
    def test_workflow_class_exists(self):
        assert hasattr(PublishWorkflow, "run")
