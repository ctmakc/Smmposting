"""Effectiveness scoring — compares post metrics against baseline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricsSnapshot:
    """A single metrics snapshot for comparison."""

    views: int = 0
    watch_time: float = 0.0
    retention: float = 0.0
    ctr: float = 0.0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    sentiment: float = 0.0


@dataclass
class BaselineMetrics:
    """Baseline averages for comparison (brand/format/platform level)."""

    avg_views: float = 0.0
    avg_watch_time: float = 0.0
    avg_retention: float = 0.0
    avg_ctr: float = 0.0
    avg_comments: float = 0.0
    avg_shares: float = 0.0
    avg_saves: float = 0.0
    avg_sentiment: float = 0.0


@dataclass
class EffectivenessResult:
    """Result of effectiveness evaluation."""

    score: float  # 0-100
    above_baseline: bool
    multipliers: dict[str, float]  # per-metric multiplier vs baseline
    strongest: str  # best-performing metric
    weakest: str  # worst-performing metric


class EffectivenessScorer:
    """Evaluates how well a post performed relative to baseline.

    Computes a composite effectiveness score (0-100) and per-metric
    multipliers showing how each metric compares to the baseline average.
    """

    METRIC_WEIGHTS = {
        "views": 0.20,
        "watch_time": 0.15,
        "retention": 0.20,
        "ctr": 0.15,
        "comments": 0.10,
        "shares": 0.10,
        "saves": 0.05,
        "sentiment": 0.05,
    }

    def evaluate(
        self, snapshot: MetricsSnapshot, baseline: BaselineMetrics
    ) -> EffectivenessResult:
        multipliers = self._compute_multipliers(snapshot, baseline)

        weighted_score = sum(
            self.METRIC_WEIGHTS[k] * self._multiplier_to_score(multipliers[k])
            for k in self.METRIC_WEIGHTS
        )

        score = max(0.0, min(100.0, weighted_score))

        strongest = max(multipliers, key=multipliers.get)  # type: ignore[arg-type]
        weakest = min(multipliers, key=multipliers.get)  # type: ignore[arg-type]

        return EffectivenessResult(
            score=round(score, 1),
            above_baseline=score >= 50.0,
            multipliers={k: round(v, 2) for k, v in multipliers.items()},
            strongest=strongest,
            weakest=weakest,
        )

    def _compute_multipliers(
        self, snapshot: MetricsSnapshot, baseline: BaselineMetrics
    ) -> dict[str, float]:
        def safe_ratio(actual: float, avg: float) -> float:
            if avg <= 0:
                return 1.0 if actual <= 0 else 2.0
            return actual / avg

        return {
            "views": safe_ratio(snapshot.views, baseline.avg_views),
            "watch_time": safe_ratio(snapshot.watch_time, baseline.avg_watch_time),
            "retention": safe_ratio(snapshot.retention, baseline.avg_retention),
            "ctr": safe_ratio(snapshot.ctr, baseline.avg_ctr),
            "comments": safe_ratio(snapshot.comments, baseline.avg_comments),
            "shares": safe_ratio(snapshot.shares, baseline.avg_shares),
            "saves": safe_ratio(snapshot.saves, baseline.avg_saves),
            "sentiment": safe_ratio(
                (snapshot.sentiment + 1.0) / 2.0,
                (baseline.avg_sentiment + 1.0) / 2.0,
            ),
        }

    @staticmethod
    def _multiplier_to_score(multiplier: float) -> float:
        """Convert a multiplier (0..inf) to a 0-100 score.

        multiplier=1.0 -> 50 (baseline)
        multiplier=2.0 -> 75
        multiplier=0.5 -> 25
        multiplier=0.0 -> 0
        """
        if multiplier <= 0:
            return 0.0
        # Linear mapping: 1.0 -> 50, capped at 100
        return min(100.0, multiplier * 50.0)
