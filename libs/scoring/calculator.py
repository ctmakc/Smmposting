"""Score calculators for content ideas."""

from dataclasses import dataclass


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class PriorityScoreInput:
    trend_score: float = 0.0
    gap_score: float = 0.0
    brand_fit: float = 0.0
    effort_inverse: float = 0.0
    conversion_intent: float = 0.0


@dataclass
class RiskScoreInput:
    claim_risk: float = 0.0
    competitor_risk: float = 0.0
    policy_violation: float = 0.0
    ambiguity: float = 0.0
    platform_risk: float = 0.0


class PriorityScoreCalculator:
    """
    PriorityScore (0–100) =
        0.35 * TrendScore
      + 0.25 * GapScore
      + 0.20 * BrandFit
      + 0.10 * EffortInverse
      + 0.10 * ConversionIntent
    """

    WEIGHTS = (0.35, 0.25, 0.20, 0.10, 0.10)

    def calculate(self, inp: PriorityScoreInput) -> float:
        raw = (
            self.WEIGHTS[0] * inp.trend_score
            + self.WEIGHTS[1] * inp.gap_score
            + self.WEIGHTS[2] * inp.brand_fit
            + self.WEIGHTS[3] * inp.effort_inverse
            + self.WEIGHTS[4] * inp.conversion_intent
        )
        return _clamp(raw)


class RiskScoreCalculator:
    """
    RiskScore (0–100) =
        0.30 * ClaimRisk
      + 0.25 * CompetitorRisk
      + 0.15 * PolicyViolation
      + 0.15 * Ambiguity
      + 0.15 * PlatformRisk
    """

    WEIGHTS = (0.30, 0.25, 0.15, 0.15, 0.15)

    def calculate(self, inp: RiskScoreInput) -> float:
        raw = (
            self.WEIGHTS[0] * inp.claim_risk
            + self.WEIGHTS[1] * inp.competitor_risk
            + self.WEIGHTS[2] * inp.policy_violation
            + self.WEIGHTS[3] * inp.ambiguity
            + self.WEIGHTS[4] * inp.platform_risk
        )
        return _clamp(raw)
