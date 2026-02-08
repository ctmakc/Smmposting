"""Tests for prompt template renderer."""

from pathlib import Path

from libs.llm.prompts import PromptRenderer

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class TestPromptRenderer:
    def setup_method(self):
        self.renderer = PromptRenderer(PROMPTS_DIR)

    def test_gap_analysis_template(self):
        result = self.renderer.render(
            "strategist/gap_analysis.j2",
            brand_name="TestBrand",
            niches=["tech", "ai"],
            locale="en",
            sources=[
                {"title": "AI Video", "author": "bob", "platform": "tiktok",
                 "features": {"hook_type": "question"}, "scores": {"views": 1000}},
            ],
            questions=["How to use AI?"],
            archive=[{"title": "Old AI Post", "format": "listicle"}],
        )
        assert "TestBrand" in result
        assert "tech, ai" in result
        assert "AI Video" in result
        assert "How to use AI?" in result
        assert "JSON" in result

    def test_idea_generation_template(self):
        result = self.renderer.render(
            "strategist/idea_generation.j2",
            brand_name="MyBrand",
            niches=["finance"],
            locale="en",
            gaps=[{"topic": "budgeting", "gap_type": "angle_gap",
                   "opportunity_score": 75, "rationale": "No good content"}],
            patterns=[{"description": "listicle pattern", "effectiveness_score": 80}],
            forbidden_topics=["crypto"],
            num_ideas=5,
        )
        assert "MyBrand" in result
        assert "budgeting" in result
        assert "crypto" in result
        assert "5" in result

    def test_script_generation_template(self):
        result = self.renderer.render(
            "scriptwriter/script_generation.j2",
            title="Test Video",
            angle="tutorial",
            persona="beginner",
            format="listicle",
            forbidden_topics=["politics"],
            forbidden_claims=[],
            vocabulary_preferred=["awesome"],
            vocabulary_banned=["sucks"],
            pattern_description="fast-paced hook",
        )
        assert "Test Video" in result
        assert "tutorial" in result
        assert "politics" in result
        assert "awesome" in result

    def test_qc_template(self):
        result = self.renderer.render(
            "qc/quality_check.j2",
            hook_variants=["Hook 1", "Hook 2", "Hook 3"],
            script_sections={
                "hook": "The hook text",
                "body": "The body",
                "payoff": "Payoff",
                "cta": "CTA",
            },
            forbidden_topics=["gambling"],
            forbidden_claims=["guaranteed returns"],
            vocabulary_banned=["bro"],
            risk_threshold=50,
        )
        assert "Hook 1" in result
        assert "gambling" in result
        assert "50" in result
