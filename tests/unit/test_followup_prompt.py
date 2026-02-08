"""Tests for the follow-up idea generation prompt template."""

from libs.llm.prompts import PromptRenderer


class TestFollowUpPrompt:
    def setup_method(self):
        self.renderer = PromptRenderer()

    def test_followup_above_baseline(self):
        prompt = self.renderer.render(
            "strategist/followup_ideas.j2",
            title="5 AI Tools You Need",
            platform="tiktok",
            views=25000,
            views_multiplier=2.5,
            retention=60.0,
            retention_multiplier=1.3,
            shares=80,
            shares_multiplier=4.0,
            sentiment=0.8,
            sentiment_multiplier=1.2,
            effectiveness_score=72.0,
            strongest="views",
            weakest="sentiment",
            top_questions=["What tools?", "Part 2?"],
            brand_name="TechBrand",
            niches=["tech", "ai"],
            above_baseline=True,
            num_ideas=3,
        )
        assert "above" in prompt
        assert "TechBrand" in prompt
        assert "Part 2" in prompt.lower() or "sequel" in prompt.lower()
        assert "JSON" in prompt

    def test_followup_below_baseline(self):
        prompt = self.renderer.render(
            "strategist/followup_ideas.j2",
            title="Budget Tips",
            platform="youtube",
            views=3000,
            views_multiplier=0.3,
            retention=25.0,
            retention_multiplier=0.6,
            shares=5,
            shares_multiplier=0.25,
            sentiment=-0.1,
            sentiment_multiplier=0.7,
            effectiveness_score=28.0,
            strongest="retention",
            weakest="shares",
            top_questions=["More details?"],
            brand_name="FinBrand",
            niches=["finance"],
            above_baseline=False,
            num_ideas=3,
        )
        assert "below" in prompt
        assert "FinBrand" in prompt
        assert "underperformed" in prompt.lower() or "reworked" in prompt.lower()

    def test_followup_empty_questions(self):
        prompt = self.renderer.render(
            "strategist/followup_ideas.j2",
            title="Test",
            platform="instagram",
            views=0,
            views_multiplier=0.0,
            retention=0.0,
            retention_multiplier=0.0,
            shares=0,
            shares_multiplier=0.0,
            sentiment=0.0,
            sentiment_multiplier=0.0,
            effectiveness_score=0.0,
            strongest="views",
            weakest="shares",
            top_questions=[],
            brand_name="Brand",
            niches=[],
            above_baseline=False,
            num_ideas=3,
        )
        assert "Brand" in prompt
