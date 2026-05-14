from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from elek_mcp_demo.domain.models import DocSection, EvidenceItem


HEADING_PATTERN = re.compile(r"^##\s+(?P<title>.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedSection:
    section_id: str
    title: str
    source_file: str
    content: str


def default_docs_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "docs"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def load_sections(docs_dir: Path | None = None) -> list[ParsedSection]:
    docs_path = docs_dir or default_docs_dir()
    sections: list[ParsedSection] = []

    for path in sorted(docs_path.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        matches = list(HEADING_PATTERN.finditer(text))
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            title = match.group("title").strip()
            content = text[start:end].strip()
            sections.append(
                ParsedSection(
                    section_id=f"{path.stem}:{slugify(title)}",
                    title=title,
                    source_file=path.name,
                    content=content,
                )
            )

    return sections


def search_docs(query: str, limit: int = 3, docs_dir: Path | None = None) -> list[EvidenceItem]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    query_terms = tokenize(query)
    scored: list[tuple[float, ParsedSection]] = []

    for section in load_sections(docs_dir):
        searchable = f"{section.title} {section.content}"
        terms = tokenize(searchable)
        overlap = query_terms.intersection(terms)
        phrase_bonus = 1 if query.lower() in searchable.lower() else 0
        score = len(overlap) + phrase_bonus
        if score > 0:
            scored.append((float(score), section))

    scored.sort(key=lambda item: (-item[0], item[1].source_file, item[1].title))
    return [
        EvidenceItem(
            section_id=section.section_id,
            title=section.title,
            source_file=section.source_file,
            snippet=make_snippet(section.content),
            score=score,
        )
        for score, section in scored[:limit]
    ]


def get_doc_section(section_id: str, docs_dir: Path | None = None) -> DocSection:
    for section in load_sections(docs_dir):
        if section.section_id == section_id:
            return DocSection(
                section_id=section.section_id,
                title=section.title,
                source_file=section.source_file,
                snippet=make_snippet(section.content),
                content=section.content,
            )
    raise KeyError(f"Unknown section_id: {section_id}")


def tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(term) > 2}


def make_snippet(text: str, max_chars: int = 260) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."
