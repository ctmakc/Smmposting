"""Tests for the pre-publish safety gate."""

from libs.publishing.safety import SafetyGate


class TestSafetyGate:
    def setup_method(self):
        self.gate = SafetyGate()

    def test_all_checks_pass(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="This is a safe script about AI tools.",
            forbidden_topics=[],
            forbidden_claim_patterns=[],
            competitor_mentions=[],
        )
        assert result.passed is True
        assert result.violations == []

    def test_risk_score_exceeds_threshold(self):
        result = self.gate.check(
            risk_score=65.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Some script text.",
            forbidden_topics=[],
            forbidden_claim_patterns=[],
            competitor_mentions=[],
        )
        assert result.passed is False
        assert any("Risk score" in v for v in result.violations)

    def test_qc_status_not_approved(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="pending",
            script_text="Some script text.",
            forbidden_topics=[],
            forbidden_claim_patterns=[],
            competitor_mentions=[],
        )
        assert result.passed is False
        assert any("QC status" in v for v in result.violations)

    def test_forbidden_topic_detected(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="This script talks about gambling and casinos.",
            forbidden_topics=["gambling"],
            forbidden_claim_patterns=[],
            competitor_mentions=[],
        )
        assert result.passed is False
        assert any("gambling" in v for v in result.violations)

    def test_forbidden_claim_pattern_regex(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Guaranteed 100% returns on investment!",
            forbidden_topics=[],
            forbidden_claim_patterns=[r"guaranteed\s+\d+%"],
            competitor_mentions=[],
        )
        assert result.passed is False
        assert any("pattern" in v.lower() for v in result.violations)

    def test_forbidden_claim_plain_text_fallback(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="We guarantee income for all users.",
            forbidden_topics=[],
            forbidden_claim_patterns=["guarantee income"],
            competitor_mentions=[],
        )
        assert result.passed is False

    def test_competitor_mention_detected(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Our product is way better than CompetitorX.",
            forbidden_topics=[],
            forbidden_claim_patterns=[],
            competitor_mentions=["CompetitorX"],
        )
        assert result.passed is False
        assert any("CompetitorX" in v for v in result.violations)

    def test_multiple_violations(self):
        result = self.gate.check(
            risk_score=80.0,
            risk_threshold=50,
            qc_status="rejected",
            script_text="Gambling tips guaranteed to work! CompetitorX sucks.",
            forbidden_topics=["gambling"],
            forbidden_claim_patterns=["guaranteed"],
            competitor_mentions=["CompetitorX"],
        )
        assert result.passed is False
        assert len(result.violations) == 5  # risk, qc, topic, claim, competitor

    def test_case_insensitive_matching(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Let's talk about GAMBLING strategies.",
            forbidden_topics=["gambling"],
            forbidden_claim_patterns=[],
            competitor_mentions=[],
        )
        assert result.passed is False

    def test_invalid_regex_falls_back_to_plain_text(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="This has [invalid pattern in it.",
            forbidden_topics=[],
            forbidden_claim_patterns=[r"[invalid"],  # broken regex
            competitor_mentions=[],
        )
        assert result.passed is False
        assert any("claim" in v.lower() for v in result.violations)

    def test_invalid_regex_fallback_no_match(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Totally safe content here.",
            forbidden_topics=[],
            forbidden_claim_patterns=[r"[invalid"],  # broken regex, no match
            competitor_mentions=[],
        )
        assert result.passed is True

    def test_empty_script_text(self):
        result = self.gate.check(
            risk_score=20.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="",
            forbidden_topics=["gambling"],
            forbidden_claim_patterns=[r"guaranteed\s+\d+%"],
            competitor_mentions=["CompetitorX"],
        )
        assert result.passed is True

    def test_edge_case_exact_threshold(self):
        result = self.gate.check(
            risk_score=50.0,
            risk_threshold=50,
            qc_status="approved",
            script_text="Safe content.",
            forbidden_topics=[],
            forbidden_claim_patterns=[],
            competitor_mentions=[],
        )
        assert result.passed is True  # equal to threshold is OK
