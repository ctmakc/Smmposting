"""Generate worker workflows — script generation with QC loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from apps.worker_generate.activities import (
        GenerateScriptInput,
        GenerateScriptOutput,
        QCCheckInput,
        QCCheckOutput,
        RewriteScriptInput,
        RewriteScriptOutput,
        generate_script_activity,
        qc_check_activity,
        rewrite_script_activity,
    )

TASK_QUEUE = "generate"
MAX_REWRITES = 3


@dataclass
class ScriptGenerationInput:
    idea_id: str
    title: str
    angle: str
    persona: str
    format: str
    forbidden_topics: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    vocabulary_preferred: list[str] = field(default_factory=list)
    vocabulary_banned: list[str] = field(default_factory=list)
    pattern_description: str = ""
    risk_threshold: int = 50
    max_rewrites: int = MAX_REWRITES


@dataclass
class ScriptGenerationOutput:
    script_id: str
    approved: bool
    qc_score: int
    version: int
    rewrite_count: int


@workflow.defn
class ScriptGenerationWorkflow:
    """Workflow: generate script, QC check, auto-rewrite loop.

    - Generates a script via LLM
    - Runs QC check
    - If QC fails, auto-rewrites up to N times
    - Final result: APPROVED or NEEDS_APPROVAL
    """

    @workflow.run
    async def run(self, inp: ScriptGenerationInput) -> ScriptGenerationOutput:
        workflow.logger.info("script_generation_start", idea_id=inp.idea_id)

        retry = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        # Step 1: Generate initial script
        gen_result: GenerateScriptOutput = await workflow.execute_activity(
            generate_script_activity,
            GenerateScriptInput(
                idea_id=inp.idea_id,
                title=inp.title,
                angle=inp.angle,
                persona=inp.persona,
                format=inp.format,
                forbidden_topics=inp.forbidden_topics,
                forbidden_claims=inp.forbidden_claims,
                vocabulary_preferred=inp.vocabulary_preferred,
                vocabulary_banned=inp.vocabulary_banned,
                pattern_description=inp.pattern_description,
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry,
        )

        script_id = gen_result.script_id
        version = gen_result.version
        rewrite_count = 0

        # Step 2: QC loop
        for attempt in range(inp.max_rewrites + 1):
            qc_result: QCCheckOutput = await workflow.execute_activity(
                qc_check_activity,
                QCCheckInput(
                    script_id=script_id,
                    hook_variants=gen_result.hook_variants,
                    script_sections={},  # Will be read from DB by activity
                    forbidden_topics=inp.forbidden_topics,
                    forbidden_claims=inp.forbidden_claims,
                    vocabulary_banned=inp.vocabulary_banned,
                    risk_threshold=inp.risk_threshold,
                ),
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=retry,
            )

            if qc_result.approved:
                workflow.logger.info(
                    "script_approved",
                    script_id=script_id,
                    score=qc_result.score,
                    attempt=attempt,
                )
                return ScriptGenerationOutput(
                    script_id=script_id,
                    approved=True,
                    qc_score=qc_result.score,
                    version=version,
                    rewrite_count=rewrite_count,
                )

            # QC failed — rewrite if attempts remain
            if attempt < inp.max_rewrites:
                workflow.logger.info(
                    "script_rewrite",
                    script_id=script_id,
                    attempt=attempt + 1,
                    issues=len(qc_result.issues),
                )

                qc_notes = "; ".join(
                    [f"[{i['severity']}] {i['description']}" for i in qc_result.issues]
                    or qc_result.suggestions
                )

                rewrite_result: RewriteScriptOutput = await workflow.execute_activity(
                    rewrite_script_activity,
                    RewriteScriptInput(
                        script_id=script_id,
                        qc_notes=qc_notes,
                        previous_sections={},
                        forbidden_topics=inp.forbidden_topics,
                        forbidden_claims=inp.forbidden_claims,
                        vocabulary_preferred=inp.vocabulary_preferred,
                        vocabulary_banned=inp.vocabulary_banned,
                    ),
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry,
                )

                version = rewrite_result.new_version
                rewrite_count += 1

        # Exhausted rewrites — needs manual approval
        workflow.logger.info(
            "script_needs_approval",
            script_id=script_id,
            rewrites=rewrite_count,
        )

        return ScriptGenerationOutput(
            script_id=script_id,
            approved=False,
            qc_score=qc_result.score,
            version=version,
            rewrite_count=rewrite_count,
        )
