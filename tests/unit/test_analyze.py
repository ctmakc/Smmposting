"""Tests for analyze worker dataclasses."""

from apps.worker_analyze.activities import (
    GapAnalysisInput,
    GapAnalysisOutput,
    IdeaGenerationInput,
    IdeaGenerationOutput,
)
from apps.worker_analyze.workflows import ContentPlanningInput, ContentPlanningOutput


class TestAnalyzeDataclasses:
    def test_gap_analysis_input(self):
        inp = GapAnalysisInput(
            brand_id="b1", brand_name="Test", niches=["tech"], locale="en", sources=[]
        )
        assert inp.questions == []
        assert inp.archive == []

    def test_gap_analysis_output(self):
        out = GapAnalysisOutput(gaps=[{"topic": "ai"}], top_questions=["How?"])
        assert len(out.gaps) == 1

    def test_idea_generation_input(self):
        inp = IdeaGenerationInput(
            brand_id="b1", brand_name="Test", niches=["tech"],
            locale="en", gaps=[{"topic": "ai"}]
        )
        assert inp.num_ideas == 3
        assert inp.forbidden_topics == []

    def test_idea_generation_output(self):
        out = IdeaGenerationOutput(ideas_created=3, idea_ids=["a", "b", "c"])
        assert out.ideas_created == 3

    def test_content_planning_input(self):
        inp = ContentPlanningInput(
            brand_id="b1", brand_name="Test", niches=["tech"], locale="en"
        )
        assert inp.num_ideas == 3
        assert inp.sources == []

    def test_content_planning_output(self):
        out = ContentPlanningOutput(
            gaps_found=2, ideas_created=3,
            idea_ids=["a", "b", "c"], top_questions=["Q?"]
        )
        assert out.gaps_found == 2
