#!/usr/bin/env python3
"""Build evergreen article drafts from INNOVA AI content packs.

The source packs live outside this repository and contain CMS-ready service pages.
This script repackages them into long-form external article drafts that are easier
to syndicate later to Medium, vc.ru, and similar platforms.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path("/data/projects/!products/social-posting/Smmposting")
SOURCE_ROOT = Path("/data/Документы/INNOVA AI TRANSFORMATYION/ai-sections-structure")
OUTPUT_ROOT = ROOT / "content" / "evergreen_articles"


PACKS = [
    {
        "brand_slug": "crystal",
        "brand_name": "Crystal",
        "source": SOURCE_ROOT / "crystal" / "02-crystal-ai-content-pack.md",
        "platform_targets": ["medium", "vc_ru", "teletype"],
        "tags": ["ai", "automation", "international-business", "operations"],
    },
    {
        "brand_slug": "mmix",
        "brand_name": "MMIX",
        "source": SOURCE_ROOT / "mmix" / "02-mmix-ai-content-pack.md",
        "platform_targets": ["medium", "vc_ru", "teletype"],
        "tags": ["ai", "marketing", "automation", "agency-ops"],
    },
    {
        "brand_slug": "blocons",
        "brand_name": "Blocons",
        "source": SOURCE_ROOT / "blocons" / "02-web3-ai-content-pack.md",
        "platform_targets": ["medium", "vc_ru", "teletype"],
        "tags": ["ai", "web3", "crypto", "compliance"],
    },
    {
        "brand_slug": "legal",
        "brand_name": "Legal Solutions",
        "source": SOURCE_ROOT / "legal" / "02-legal-ai-content-pack.md",
        "platform_targets": ["medium", "vc_ru", "teletype"],
        "tags": ["ai", "legal", "compliance", "governance"],
    },
]


@dataclass
class Page:
    section_title: str
    url: str
    seo_title: str
    meta_description: str
    h1: str
    main_text: str
    faq: list[tuple[str, str]]


def clean_value(line: str) -> str:
    return re.sub(r"^\*\*[^:]+:\*\*\s*", "", line).strip()


def parse_pack(path: Path) -> list[Page]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"^##\s+", text, flags=re.M)
    pages: list[Page] = []
    for chunk in sections[1:]:
        lines = chunk.splitlines()
        section_title = lines[0].strip()
        body = "\n".join(lines[1:])

        url = re.search(r"\*\*URL:\*\*\s*`([^`]+)`", body)
        seo_title = re.search(r"\*\*SEO title:\*\*\s*(.+)", body)
        meta_description = re.search(r"\*\*Meta description:\*\*\s*(.+)", body)
        h1 = re.search(r"\*\*H1:\*\*\s*(.+)", body)
        main_match = re.search(r"\*\*Main text:\*\*\n\n(.+?)\n\n\*\*FAQ:\*\*", body, flags=re.S)
        faq_match = re.search(r"\*\*FAQ:\*\*\n\n(.+?)\n\n\*\*JSON-LD:\*\*", body, flags=re.S)
        if not all([url, seo_title, meta_description, h1, main_match, faq_match]):
            continue

        faq_entries: list[tuple[str, str]] = []
        faq_blocks = re.split(r"\n(?=\*\*)", faq_match.group(1).strip())
        for block in faq_blocks:
            m = re.match(r"\*\*(.+?)\*\*\s{2,}\n(.+)", block.strip(), flags=re.S)
            if m:
                question = m.group(1).strip()
                answer = " ".join(x.strip() for x in m.group(2).strip().splitlines())
                faq_entries.append((question, answer))

        pages.append(
            Page(
                section_title=section_title,
                url=url.group(1).strip(),
                seo_title=seo_title.group(1).strip(),
                meta_description=meta_description.group(1).strip(),
                h1=h1.group(1).strip(),
                main_text=main_match.group(1).strip(),
                faq=faq_entries,
            )
        )
    return pages


def slug_from_url(url: str) -> str:
    slug = url.strip("/").replace("/", "__")
    return slug or "index"


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def build_article_title(page: Page, brand_name: str) -> str:
    base = page.h1
    if brand_name.lower() in base.lower():
        return base
    return f"{base}: практическое применение для бизнеса"


def build_article_body(page: Page) -> str:
    paragraphs = split_paragraphs(page.main_text)
    intro = paragraphs[:2]
    middle = paragraphs[2:4]
    end = paragraphs[4:]

    parts: list[str] = [f"# {page.h1}", "", page.meta_description, ""]

    if intro:
        parts.extend(intro)
        parts.append("")

    if middle:
        parts.append("## Где это дает реальную пользу")
        parts.append("")
        parts.extend(middle)
        parts.append("")

    if end:
        parts.append("## Что важно не перепутать")
        parts.append("")
        parts.extend(end)
        parts.append("")

    if page.faq:
        parts.append("## Короткие вопросы по теме")
        parts.append("")
        for question, answer in page.faq[:3]:
            parts.append(f"**{question}**")
            parts.append(answer)
            parts.append("")

    parts.append("## Что можно сделать следующим шагом")
    parts.append("")
    parts.append(
        "Обычно лучший формат старта здесь не большой проект, а разбор одного процесса, "
        "который уже создает лишнюю ручную нагрузку или риск. После этого проще понять, "
        "где automation действительно усиливает бизнес, а где лучше оставить ручной контроль."
    )
    parts.append("")
    return "\n".join(parts).strip() + "\n"


def write_article(pack: dict[str, object], page: Page) -> dict[str, object]:
    brand_slug = str(pack["brand_slug"])
    brand_name = str(pack["brand_name"])
    tags = list(pack["tags"])
    targets = list(pack["platform_targets"])

    article_slug = slug_from_url(page.url)
    out_dir = OUTPUT_ROOT / brand_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{article_slug}.md"

    title = build_article_title(page, brand_name)
    article_body = build_article_body(page)

    frontmatter = {
        "title": title,
        "brand": brand_name,
        "brand_slug": brand_slug,
        "canonical_section_url": page.url,
        "source_pack": str(pack["source"]),
        "source_h1": page.h1,
        "seo_title": page.seo_title,
        "meta_description": page.meta_description,
        "platform_targets": targets,
        "tags": tags,
        "status": "draft",
        "distribution_kind": "evergreen_article",
    }

    fm_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            fm_lines.append(f"{key}:")
            for item in value:
                fm_lines.append(f"  - {item}")
        else:
            safe = str(value).replace('"', '\\"')
            fm_lines.append(f'{key}: "{safe}"')
    fm_lines.append("---")
    fm_lines.append("")

    out_path.write_text("\n".join(fm_lines) + article_body, encoding="utf-8")

    return {
        "brand_slug": brand_slug,
        "brand_name": brand_name,
        "slug": article_slug,
        "title": title,
        "path": str(out_path.relative_to(ROOT)),
        "canonical_section_url": page.url,
        "platform_targets": targets,
        "tags": tags,
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_entries: list[dict[str, object]] = []

    for pack in PACKS:
        pages = parse_pack(Path(pack["source"]))
        for page in pages:
            manifest_entries.append(write_article(pack, page))

    manifest = {
        "generated_from": "INNOVA AI section packs",
        "article_count": len(manifest_entries),
        "articles": manifest_entries,
    }
    (OUTPUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "README.md").write_text(
        "# Evergreen Article Import Pack\n\n"
        "This folder contains external-blog article drafts generated from the INNOVA AI section packs.\n\n"
        "Purpose:\n"
        "- keep rewritten article-style drafts close to the posting engine\n"
        "- make later Medium / vc.ru / Teletype ingestion straightforward\n"
        "- preserve source linkage back to the service-page content packs\n\n"
        "Structure:\n"
        "- `manifest.json` — machine-readable list of all drafts\n"
        "- `<brand>/...md` — per-article markdown files with frontmatter\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
