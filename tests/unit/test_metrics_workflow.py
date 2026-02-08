"""Tests for the metrics collection workflow and activities."""

from apps.worker_metrics.activities import (
    EvaluateEffectivenessInput,
    EvaluateEffectivenessOutput,
    FetchMetricsInput,
    FetchMetricsOutput,
    GenerateFollowUpInput,
    GenerateFollowUpOutput,
    StoreMetricsInput,
    StoreMetricsOutput,
    UpdatePatternOutput,
)
from apps.worker_metrics.workflows import (
    METRICS_WINDOWS,
    MetricsCollectionInput,
    MetricsCollectionOutput,
    MetricsCollectionWorkflow,
)


class TestMetricsDataclasses:
    def test_fetch_metrics_input(self):
        inp = FetchMetricsInput(
            post_id="p1",
            platform="tiktok",
            platform_post_url="https://tiktok.com/post/123",
            window="2h",
        )
        assert inp.window == "2h"

    def test_fetch_metrics_output_defaults(self):
        out = FetchMetricsOutput(post_id="p1", window="24h")
        assert out.views == 0
        assert out.top_questions == []

    def test_store_metrics_input(self):
        inp = StoreMetricsInput(
            post_id="p1",
            window="72h",
            views=5000,
            retention=45.5,
        )
        assert inp.views == 5000

    def test_store_metrics_output(self):
        out = StoreMetricsOutput(metrics_id="m1")
        assert out.metrics_id == "m1"

    def test_evaluate_effectiveness_input(self):
        inp = EvaluateEffectivenessInput(
            post_id="p1",
            views=15000,
            watch_time=45.0,
            retention=60.0,
            ctr=5.5,
        )
        assert inp.views == 15000

    def test_evaluate_effectiveness_output(self):
        out = EvaluateEffectivenessOutput(
            effectiveness_score=72.5,
            above_baseline=True,
            strongest="views",
            weakest="sentiment",
            multipliers={"views": 1.5, "retention": 1.2},
        )
        assert out.above_baseline is True
        assert out.strongest == "views"

    def test_update_pattern_output(self):
        out = UpdatePatternOutput(pattern_id="pat1", updated=True)
        assert out.updated is True

    def test_update_pattern_not_found(self):
        out = UpdatePatternOutput(pattern_id=None, updated=False)
        assert out.updated is False

    def test_generate_followup_input(self):
        inp = GenerateFollowUpInput(
            post_id="p1",
            title="Test Video",
            platform="tiktok",
            brand_id="b1",
            brand_name="TestBrand",
            niches=["tech"],
            views=20000,
            retention=55.0,
            shares=100,
            sentiment=0.6,
            effectiveness_score=70.0,
            above_baseline=True,
            strongest="views",
            weakest="sentiment",
        )
        assert inp.num_ideas == 3  # default

    def test_generate_followup_output(self):
        out = GenerateFollowUpOutput(ideas_created=3, idea_ids=["i1", "i2", "i3"])
        assert len(out.idea_ids) == 3


class TestMetricsCollectionWorkflowInput:
    def test_input_defaults(self):
        inp = MetricsCollectionInput(
            post_id="p1",
            platform="youtube",
            platform_post_url="https://youtube.com/watch?v=abc",
            title="My Video",
            brand_id="b1",
            brand_name="Brand",
        )
        assert inp.niches == []
        assert inp.num_followup_ideas == 3

    def test_output(self):
        out = MetricsCollectionOutput(
            post_id="p1",
            windows_collected=["2h", "24h", "72h"],
            final_effectiveness=65.0,
            above_baseline=True,
            pattern_updated=True,
            followup_ideas_created=3,
        )
        assert len(out.windows_collected) == 3
        assert out.pattern_updated is True


class TestMetricsWindows:
    def test_three_windows_defined(self):
        assert len(METRICS_WINDOWS) == 3
        names = [name for name, _ in METRICS_WINDOWS]
        assert names == ["2h", "24h", "72h"]


class TestWorkflowDefinition:
    def test_workflow_class_exists(self):
        assert hasattr(MetricsCollectionWorkflow, "run")
