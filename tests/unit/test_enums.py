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
        expected = {"pending", "approved", "rejected", "rewriting"}
        assert {s.value for s in QCStatus} == expected

    def test_string_representation(self):
        assert QCStatus.PENDING == "pending"
        assert QCStatus.APPROVED == "approved"


class TestPublishStatus:
    def test_all_statuses(self):
        expected = {"draft", "scheduled", "publishing", "published", "failed"}
        assert {s.value for s in PublishStatus} == expected

    def test_string_representation(self):
        assert PublishStatus.DRAFT == "draft"
        assert PublishStatus.PUBLISHED == "published"


class TestRunStatus:
    def test_all_statuses(self):
        expected = {"running", "completed", "failed", "cancelled"}
        assert {s.value for s in RunStatus} == expected

    def test_string_representation(self):
        assert RunStatus.RUNNING == "running"
        assert RunStatus.COMPLETED == "completed"
