"""Domain enumerations."""

import enum


class IdeaStatus(str, enum.Enum):
    BACKLOG = "backlog"
    RESEARCHED = "researched"
    PLANNED = "planned"
    SCRIPTING = "scripting"
    QC = "qc"
    NEEDS_APPROVAL = "needs_approval"
    PRODUCING = "producing"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    LEARNING = "learning"
    ARCHIVED = "archived"


class QCStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REWRITING = "rewriting"


class PublishStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class RunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricsWindow(str, enum.Enum):
    H2 = "2h"
    H24 = "24h"
    H72 = "72h"
