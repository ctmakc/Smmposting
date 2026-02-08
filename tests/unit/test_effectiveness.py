"""Tests for the effectiveness scoring system."""

from libs.scoring.effectiveness import (
    BaselineMetrics,
    EffectivenessScorer,
    MetricsSnapshot,
)


class TestEffectivenessScorer:
    def setup_method(self):
        self.scorer = EffectivenessScorer()
        self.baseline = BaselineMetrics(
            avg_views=10000.0,
            avg_watch_time=30.0,
            avg_retention=45.0,
            avg_ctr=4.0,
            avg_comments=50.0,
            avg_shares=20.0,
            avg_saves=10.0,
            avg_sentiment=0.3,
        )

    def test_exactly_baseline_scores_50(self):
        snapshot = MetricsSnapshot(
            views=10000,
            watch_time=30.0,
            retention=45.0,
            ctr=4.0,
            comments=50,
            shares=20,
            saves=10,
            sentiment=0.3,
        )
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert result.score == 50.0
        assert result.above_baseline is True

    def test_double_baseline_scores_above_50(self):
        snapshot = MetricsSnapshot(
            views=20000,
            watch_time=60.0,
            retention=90.0,
            ctr=8.0,
            comments=100,
            shares=40,
            saves=20,
            sentiment=0.3,
        )
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert result.score > 50.0
        assert result.above_baseline is True

    def test_half_baseline_scores_below_50(self):
        snapshot = MetricsSnapshot(
            views=5000,
            watch_time=15.0,
            retention=22.5,
            ctr=2.0,
            comments=25,
            shares=10,
            saves=5,
            sentiment=0.3,
        )
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert result.score < 50.0
        assert result.above_baseline is False

    def test_zero_metrics(self):
        snapshot = MetricsSnapshot()
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert result.score >= 0.0
        assert result.above_baseline is False

    def test_zero_baseline(self):
        baseline = BaselineMetrics()
        snapshot = MetricsSnapshot(views=1000)
        result = self.scorer.evaluate(snapshot, baseline)
        assert result.score >= 0.0

    def test_strongest_and_weakest(self):
        snapshot = MetricsSnapshot(
            views=50000,  # 5x baseline — strongest
            watch_time=30.0,
            retention=45.0,
            ctr=4.0,
            comments=50,
            shares=20,
            saves=10,
            sentiment=-0.5,  # below — weakest
        )
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert result.strongest == "views"
        assert result.weakest == "sentiment"

    def test_multipliers_present(self):
        snapshot = MetricsSnapshot(
            views=10000,
            watch_time=30.0,
            retention=45.0,
            ctr=4.0,
            comments=50,
            shares=20,
            saves=10,
            sentiment=0.3,
        )
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert "views" in result.multipliers
        assert "retention" in result.multipliers
        assert len(result.multipliers) == 8

    def test_score_clamped_to_100(self):
        snapshot = MetricsSnapshot(
            views=100000,
            watch_time=300.0,
            retention=100.0,
            ctr=40.0,
            comments=500,
            shares=200,
            saves=100,
            sentiment=1.0,
        )
        result = self.scorer.evaluate(snapshot, self.baseline)
        assert result.score <= 100.0

    def test_score_clamped_to_0(self):
        snapshot = MetricsSnapshot(sentiment=-1.0)
        baseline = BaselineMetrics(avg_sentiment=0.9)
        result = self.scorer.evaluate(snapshot, baseline)
        assert result.score >= 0.0

    def test_multiplier_to_score_mapping(self):
        assert self.scorer._multiplier_to_score(1.0) == 50.0
        assert self.scorer._multiplier_to_score(2.0) == 100.0
        assert self.scorer._multiplier_to_score(0.5) == 25.0
        assert self.scorer._multiplier_to_score(0.0) == 0.0
