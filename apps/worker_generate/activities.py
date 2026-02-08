"""Generate worker activities — script creation, QC check, rewrite."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field

import structlog
from temporalio import activity

from libs.db.enums import QCStatus
from libs.db.models.script import Script
from libs.db.session import async_session
from libs.llm.mock import MockLLMClient
from libs.llm.prompts import PromptRenderer

logger = structlog.get_logger()


# --- Data classes ---


@dataclass
class GenerateScriptInput:
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


@dataclass
class GenerateScriptOutput:
    script_id: str
    hook_variants: list[str]
    version: int


@dataclass
class QCCheckInput:
    script_id: str
    hook_variants: list[str]
    script_sections: dict
    forbidden_topics: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    vocabulary_banned: list[str] = field(default_factory=list)
    risk_threshold: int = 50


@dataclass
class QCCheckOutput:
    approved: bool
    score: int
    issues: list[dict]
    suggestions: list[str]


@dataclass
class RewriteScriptInput:
    script_id: str
    qc_notes: str
    previous_sections: dict
    forbidden_topics: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    vocabulary_preferred: list[str] = field(default_factory=list)
    vocabulary_banned: list[str] = field(default_factory=list)


@dataclass
class RewriteScriptOutput:
    script_id: str
    new_version: int


# --- Activities ---


@activity.defn
async def generate_script_activity(inp: GenerateScriptInput) -> GenerateScriptOutput:
    """Generate a script for a content idea using LLM."""
    logger.info("generate_script_start", idea_id=inp.idea_id)

    renderer = PromptRenderer()
    prompt = renderer.render(
        "scriptwriter/script_generation.j2",
        title=inp.title,
        angle=inp.angle,
        persona=inp.persona,
        format=inp.format,
        forbidden_topics=inp.forbidden_topics,
        forbidden_claims=inp.forbidden_claims,
        vocabulary_preferred=inp.vocabulary_preferred,
        vocabulary_banned=inp.vocabulary_banned,
        pattern_description=inp.pattern_description,
    )

    llm = MockLLMClient()
    response = await llm.generate_structured(prompt, system="You are an expert scriptwriter.")
    result = json.loads(response.content)

    script_id = str(uuid.uuid4())
    session = await async_session()
    try:
        script = Script(
            id=uuid.UUID(script_id),
            idea_id=uuid.UUID(inp.idea_id),
            version=1,
            hook_variants=result.get("hook_variants", []),
            script_sections=result.get("script_sections", {}),
            on_screen_text=result.get("on_screen_text", {}),
            broll_list=result.get("broll_list", []),
            qc_status=QCStatus.PENDING,
            generation_meta={
                "model": response.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
        )
        session.add(script)
        await session.commit()
        logger.info("generate_script_done", script_id=script_id)
    except Exception:
        await session.rollback()
        logger.exception("generate_script_failed")
        raise
    finally:
        await session.close()

    return GenerateScriptOutput(
        script_id=script_id,
        hook_variants=result.get("hook_variants", []),
        version=1,
    )


@activity.defn
async def qc_check_activity(inp: QCCheckInput) -> QCCheckOutput:
    """Run quality control check on a script."""
    logger.info("qc_check_start", script_id=inp.script_id)

    renderer = PromptRenderer()
    prompt = renderer.render(
        "qc/quality_check.j2",
        hook_variants=inp.hook_variants,
        script_sections=inp.script_sections,
        forbidden_topics=inp.forbidden_topics,
        forbidden_claims=inp.forbidden_claims,
        vocabulary_banned=inp.vocabulary_banned,
        risk_threshold=inp.risk_threshold,
    )

    llm = MockLLMClient()
    response = await llm.generate_structured(prompt, system="You are a QC specialist.")
    result = json.loads(response.content)

    approved = result.get("approved", False)
    qc_status = QCStatus.APPROVED if approved else QCStatus.REJECTED
    qc_notes = "; ".join(result.get("suggestions", []))

    session = await async_session()
    try:
        script = await session.get(Script, uuid.UUID(inp.script_id))
        if script:
            script.qc_status = qc_status
            script.qc_notes = qc_notes
            await session.commit()
        logger.info("qc_check_done", script_id=inp.script_id, approved=approved)
    except Exception:
        await session.rollback()
        logger.exception("qc_check_failed")
        raise
    finally:
        await session.close()

    return QCCheckOutput(
        approved=approved,
        score=result.get("score", 0),
        issues=result.get("issues", []),
        suggestions=result.get("suggestions", []),
    )


@activity.defn
async def rewrite_script_activity(inp: RewriteScriptInput) -> RewriteScriptOutput:
    """Rewrite a script based on QC feedback."""
    logger.info("rewrite_script_start", script_id=inp.script_id)

    session = await async_session()
    try:
        original = await session.get(Script, uuid.UUID(inp.script_id))
        if not original:
            raise ValueError(f"Script {inp.script_id} not found")

        rewrite_prompt = (
            f"Rewrite this script addressing the following QC notes:\n{inp.qc_notes}\n\n"
            f"Original script sections: {json.dumps(inp.previous_sections)}"
        )

        llm = MockLLMClient()
        response = await llm.generate_structured(
            rewrite_prompt, system="You are an expert scriptwriter."
        )
        result = json.loads(response.content)

        new_version = original.version + 1
        original.version = new_version
        original.hook_variants = result.get("hook_variants", original.hook_variants)
        original.script_sections = result.get("script_sections", original.script_sections)
        original.on_screen_text = result.get("on_screen_text", original.on_screen_text)
        original.broll_list = result.get("broll_list", original.broll_list)
        original.qc_status = QCStatus.PENDING
        original.qc_notes = None
        original.generation_meta = {
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "rewrite_reason": inp.qc_notes,
        }

        await session.commit()
        logger.info("rewrite_script_done", script_id=inp.script_id, version=new_version)
    except Exception:
        await session.rollback()
        logger.exception("rewrite_script_failed")
        raise
    finally:
        await session.close()

    return RewriteScriptOutput(script_id=inp.script_id, new_version=new_version)
