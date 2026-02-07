"""Tests for domain enumerations."""

from libs.db.enums import IdeaStatus, PublishStatus, QCStatus, RunStatus


class TestIdeaStatus:
    def test_all_statuses_exist(self):
        expected = {
            "backlog", "researched", "planned", "scripting", "qc",
            "needs_approval", "producing", "scheduled", "published",
            "learning", "archived",
        }
        assert {s.value for s in IdeaStatus} == expected

    def test_string_representation(self):
        assert IdeaStatus.BACKLOG == "backlog"
        assert IdeaStatus.PUBLISHED == "published"


class TestQCStatus:
    def test_all_statuses(self):
        assert len(QCStatus) == 4


class TestPublishStatus:
    def test_all_statuses(self):
        assert len(PublishStatus) == 5


class TestRunStatus:
    def test_all_statuses(self):
        assert len(RunStatus) == 4
