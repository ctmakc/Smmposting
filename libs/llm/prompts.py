"""Jinja2-based prompt template renderer."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class PromptRenderer:
    """Renders Jinja2 prompt templates from the prompts/ directory."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        base_dir = prompts_dir or _PROMPTS_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(base_dir)),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_path: str, **kwargs) -> str:
        """Render a template file with the given variables.

        Args:
            template_path: Relative path within prompts/ (e.g. "strategist/gap_analysis.j2")
            **kwargs: Template variables
        """
        template = self._env.get_template(template_path)
        return template.render(**kwargs)
