"""Tests for scoring calculators."""

from libs.scoring.calculator import (
    PriorityScoreCalculator,
    PriorityScoreInput,
    RiskScoreCalculator,
    RiskScoreInput,
)


class TestPriorityScoreCalculator:
    def setup_method(self):
        self.calc = PriorityScoreCalculator()

    def test_all_zeros(self):
        inp = PriorityScoreInput()
        assert self.calc.calculate(inp) == 0.0

    def test_all_max(self):
        inp = PriorityScoreInput(
            trend_score=100,
            gap_score=100,
            brand_fit=100,
            effort_inverse=100,
            conversion_intent=100,
        )
        assert self.calc.calculate(inp) == 100.0

    def test_weighted_calculation(self):
        inp = PriorityScoreInput(
            trend_score=80,
            gap_score=60,
            brand_fit=70,
            effort_inverse=50,
            conversion_intent=40,
        )
        expected = 0.35 * 80 + 0.25 * 60 + 0.20 * 70 + 0.10 * 50 + 0.10 * 40
        assert self.calc.calculate(inp) == expected

    def test_clamps_above_100(self):
        inp = PriorityScoreInput(
            trend_score=200,
            gap_score=200,
            brand_fit=200,
            effort_inverse=200,
            conversion_intent=200,
        )
        assert self.calc.calculate(inp) == 100.0

    def test_clamps_below_0(self):
        inp = PriorityScoreInput(trend_score=-100, gap_score=-100)
        assert self.calc.calculate(inp) == 0.0


class TestRiskScoreCalculator:
    def setup_method(self):
        self.calc = RiskScoreCalculator()

    def test_all_zeros(self):
        inp = RiskScoreInput()
        assert self.calc.calculate(inp) == 0.0

    def test_all_max(self):
        inp = RiskScoreInput(
            claim_risk=100,
            competitor_risk=100,
            policy_violation=100,
            ambiguity=100,
            platform_risk=100,
        )
        assert self.calc.calculate(inp) == 100.0

    def test_weighted_calculation(self):
        inp = RiskScoreInput(
            claim_risk=90,
            competitor_risk=20,
            policy_violation=10,
            ambiguity=50,
            platform_risk=30,
        )
        expected = 0.30 * 90 + 0.25 * 20 + 0.15 * 10 + 0.15 * 50 + 0.15 * 30
        assert self.calc.calculate(inp) == expected

    def test_weights_sum_to_one(self):
        assert sum(RiskScoreCalculator.WEIGHTS) == 1.0
        assert sum(PriorityScoreCalculator.WEIGHTS) == 1.0
