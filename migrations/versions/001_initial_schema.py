"""Initial schema — all 10 domain entities.

Revision ID: 001_initial
Revises: None
Create Date: 2026-02-11

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- brands ---
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("timezone", sa.String(64), server_default="UTC"),
        sa.Column("default_locale", sa.String(16), server_default="en"),
        sa.Column("niches", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("platforms_enabled", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- policies ---
    op.create_table(
        "policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("forbidden_topics", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("forbidden_claim_patterns", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("competitor_rules", postgresql.JSON, server_default="{}"),
        sa.Column("risk_threshold_auto_publish", sa.Integer, server_default="50"),
        sa.Column("vocabulary", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("transcript", sa.Text, nullable=True),
        sa.Column("features", postgresql.JSON, server_default="{}"),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scores", postgresql.JSON, server_default="{}"),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- patterns ---
    op.create_table(
        "patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_bucket", sa.String(16), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("examples", postgresql.JSON, server_default="{}"),
        sa.Column("adaptation_rules", postgresql.JSON, server_default="{}"),
        sa.Column("effectiveness_score", sa.Float, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- ideas ---
    op.create_table(
        "ideas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("angle", sa.String(512), nullable=True),
        sa.Column("persona", sa.String(255), nullable=True),
        sa.Column("format", sa.String(64), nullable=True),
        sa.Column("priority_score", sa.Float, server_default="0.0"),
        sa.Column("risk_score", sa.Float, server_default="0.0"),
        sa.Column("effort_score", sa.Float, server_default="0.0"),
        sa.Column(
            "pattern_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patterns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), server_default="backlog"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- scripts ---
    op.create_table(
        "scripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("hook_variants", postgresql.JSON, server_default="[]"),
        sa.Column("script_sections", postgresql.JSON, server_default="{}"),
        sa.Column("on_screen_text", postgresql.JSON, server_default="{}"),
        sa.Column("broll_list", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("qc_status", sa.String(32), server_default="pending"),
        sa.Column("qc_notes", sa.Text, nullable=True),
        sa.Column("generation_meta", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- assets ---
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "script_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scripts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("specs", postgresql.JSON, server_default="{}"),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("provenance", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- posts ---
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "script_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scripts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("utm_params", postgresql.JSON, server_default="{}"),
        sa.Column("publish_status", sa.String(32), server_default="draft"),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- metrics ---
    op.create_table(
        "metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("window", sa.String(8), nullable=False),
        sa.Column("views", sa.Integer, server_default="0"),
        sa.Column("watch_time", sa.Float, server_default="0.0"),
        sa.Column("retention", sa.Float, server_default="0.0"),
        sa.Column("ctr", sa.Float, server_default="0.0"),
        sa.Column("comments", sa.Integer, server_default="0"),
        sa.Column("shares", sa.Integer, server_default="0"),
        sa.Column("saves", sa.Integer, server_default="0"),
        sa.Column("sentiment", sa.Float, server_default="0.0"),
        sa.Column("top_questions", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- runs ---
    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", sa.String(255), nullable=False),
        sa.Column("trigger_type", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), server_default="running"),
        sa.Column("errors", postgresql.JSON, nullable=True),
    )

    # --- Indexes ---
    op.create_index("ix_policies_brand_id", "policies", ["brand_id"])
    op.create_index("ix_patterns_brand_id", "patterns", ["brand_id"])
    op.create_index("ix_ideas_brand_id", "ideas", ["brand_id"])
    op.create_index("ix_ideas_status", "ideas", ["status"])
    op.create_index("ix_ideas_pattern_id", "ideas", ["pattern_id"])
    op.create_index("ix_scripts_idea_id", "scripts", ["idea_id"])
    op.create_index("ix_scripts_qc_status", "scripts", ["qc_status"])
    op.create_index("ix_assets_script_id", "assets", ["script_id"])
    op.create_index("ix_posts_brand_id", "posts", ["brand_id"])
    op.create_index("ix_posts_script_id", "posts", ["script_id"])
    op.create_index("ix_posts_publish_status", "posts", ["publish_status"])
    op.create_index("ix_metrics_post_id", "metrics", ["post_id"])
    op.create_index("ix_metrics_window", "metrics", ["window"])
    op.create_index("ix_runs_workflow_id", "runs", ["workflow_id"])
    op.create_index("ix_runs_status", "runs", ["status"])


def downgrade() -> None:
    op.drop_table("runs")
    op.drop_table("metrics")
    op.drop_table("posts")
    op.drop_table("assets")
    op.drop_table("scripts")
    op.drop_table("ideas")
    op.drop_table("patterns")
    op.drop_table("sources")
    op.drop_table("policies")
    op.drop_table("brands")
