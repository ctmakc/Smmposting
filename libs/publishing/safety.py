"""Pre-publish safety gate — validates content before auto-publish."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SafetyResult:
    """Outcome of a safety gate check."""

    passed: bool
    violations: list[str] = field(default_factory=list)


class SafetyGate:
    """Evaluates whether a script is safe for auto-publishing.

    Checks:
    1. risk_score <= policy threshold
    2. qc_status is APPROVED
    3. No forbidden topics in script text
    4. No forbidden claim patterns in script text
    5. No competitor mentions (from policy.competitor_rules)
    """

    def check(
        self,
        *,
        risk_score: float,
        risk_threshold: int,
        qc_status: str,
        script_text: str,
        forbidden_topics: list[str],
        forbidden_claim_patterns: list[str],
        competitor_mentions: list[str],
    ) -> SafetyResult:
        violations: list[str] = []

        # 1. Risk threshold
        if risk_score > risk_threshold:
            violations.append(
                f"Risk score {risk_score:.1f} exceeds threshold {risk_threshold}"
            )

        # 2. QC status
        if qc_status != "approved":
            violations.append(f"QC status is '{qc_status}', expected 'approved'")

        text_lower = script_text.lower()

        # 3. Forbidden topics
        for topic in forbidden_topics:
            if topic.lower() in text_lower:
                violations.append(f"Forbidden topic found: '{topic}'")

        # 4. Forbidden claim patterns (regex)
        for pattern in forbidden_claim_patterns:
            try:
                if re.search(pattern, script_text, re.IGNORECASE):
                    violations.append(f"Forbidden claim pattern matched: '{pattern}'")
            except re.error:
                if pattern.lower() in text_lower:
                    violations.append(f"Forbidden claim found: '{pattern}'")

        # 5. Competitor mentions
        for competitor in competitor_mentions:
            if competitor.lower() in text_lower:
                violations.append(f"Competitor mention found: '{competitor}'")

        return SafetyResult(passed=len(violations) == 0, violations=violations)
