"""Tests for generate worker dataclasses."""

from apps.worker_generate.activities import (
    GenerateScriptInput,
    GenerateScriptOutput,
    QCCheckInput,
    QCCheckOutput,
    RewriteScriptInput,
    RewriteScriptOutput,
)
from apps.worker_generate.workflows import ScriptGenerationInput, ScriptGenerationOutput


class TestGenerateDataclasses:
    def test_generate_script_input(self):
        inp = GenerateScriptInput(
            idea_id="i1", title="Test", angle="tutorial",
            persona="dev", format="listicle",
        )
        assert inp.forbidden_topics == []
        assert inp.pattern_description == ""

    def test_generate_script_output(self):
        out = GenerateScriptOutput(script_id="s1", hook_variants=["h1", "h2", "h3"], version=1)
        assert len(out.hook_variants) == 3

    def test_qc_check_input(self):
        inp = QCCheckInput(
            script_id="s1", hook_variants=["h1"], script_sections={"hook": "x"}
        )
        assert inp.risk_threshold == 50

    def test_qc_check_output_approved(self):
        out = QCCheckOutput(approved=True, score=90, issues=[], suggestions=["minor fix"])
        assert out.approved is True

    def test_qc_check_output_rejected(self):
        out = QCCheckOutput(
            approved=False, score=40,
            issues=[{"type": "claim_risk", "severity": "critical", "description": "bad claim"}],
            suggestions=["fix the claim"],
        )
        assert out.approved is False
        assert len(out.issues) == 1

    def test_rewrite_script_input(self):
        inp = RewriteScriptInput(
            script_id="s1", qc_notes="fix claims", previous_sections={"hook": "old"}
        )
        assert inp.vocabulary_banned == []

    def test_rewrite_script_output(self):
        out = RewriteScriptOutput(script_id="s1", new_version=2)
        assert out.new_version == 2

    def test_script_generation_input(self):
        inp = ScriptGenerationInput(
            idea_id="i1", title="Test", angle="tutorial",
            persona="dev", format="listicle",
        )
        assert inp.max_rewrites == 3
        assert inp.risk_threshold == 50

    def test_script_generation_output(self):
        out = ScriptGenerationOutput(
            script_id="s1", approved=True, qc_score=88, version=1, rewrite_count=0
        )
        assert out.approved is True
        assert out.rewrite_count == 0
