"""CV parser: turn a resume (text, PDF or DOCX) into structured data.

Baseline approach: regexes for contact details, heading detection for
sections, and the shared skill taxonomy for skills. Layout-aware PDF parsing
and entity extraction for job titles/companies/dates are open tasks
(CV-2 .. CV-5 on the live site).
"""

from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .skills import extract_skills

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
URL_RE = re.compile(r"(?:https?://|www\.)\S+|(?:linkedin\.com|github\.com)/\S+", re.IGNORECASE)

# Heading text (lower-cased, stripped of punctuation) -> section key.
SECTION_HEADINGS = {
    "summary": "summary",
    "profile": "summary",
    "about": "summary",
    "about me": "summary",
    "objective": "summary",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "employment history": "experience",
    "education": "education",
    "academic background": "education",
    "skills": "skills",
    "technical skills": "skills",
    "core skills": "skills",
    "projects": "projects",
    "personal projects": "projects",
    "certifications": "certifications",
    "certificates": "certifications",
    "awards": "awards",
    "publications": "publications",
}


@dataclass
class ParsedCV:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    links: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    sections: dict[str, list[str]] = field(default_factory=dict)
    word_count: int = 0

    @property
    def experience(self) -> list[str]:
        return self.sections.get("experience", [])

    @property
    def education(self) -> list[str]:
        return self.sections.get("education", [])

    def to_dict(self) -> dict:
        return asdict(self)


def _heading_key(line: str) -> str | None:
    cleaned = re.sub(r"[^a-z ]", "", line.lower()).strip()
    if not cleaned or len(cleaned) > 30:
        return None
    return SECTION_HEADINGS.get(cleaned)


def _guess_name(lines: list[str]) -> str | None:
    # The first short line that isn't contact info or a heading is usually the name.
    for line in lines[:5]:
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or URL_RE.search(line):
            continue
        if _heading_key(line):
            continue
        words = line.split()
        if 1 < len(words) <= 4 and all(w[:1].isupper() for w in words):
            return line
    return None


def parse_text(text: str) -> ParsedCV:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        key = _heading_key(line)
        if key:
            current = key
            sections.setdefault(key, [])
        elif current:
            sections[current].append(line.lstrip("-•*· ").strip())

    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    return ParsedCV(
        name=_guess_name(lines),
        email=email.group(0) if email else None,
        phone=phone.group(0).strip() if phone else None,
        links=[m.group(0).rstrip(".,)") for m in URL_RE.finditer(text)],
        skills=extract_skills(text),
        sections=sections,
        word_count=len(text.split()),
    )


def extract_text(data: bytes, filename: str) -> str:
    """Extract plain text from an uploaded file (.txt, .md, .pdf, .docx)."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ""}:
        return data.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - depends on extras
            raise RuntimeError("PDF support needs: pip install 'aipath[docs]'") from exc
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        try:
            import docx
        except ImportError as exc:  # pragma: no cover - depends on extras
            raise RuntimeError("DOCX support needs: pip install 'aipath[docs]'") from exc
        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs)
    raise ValueError(f"Unsupported file type: {suffix}")


def parse_file(data: bytes, filename: str) -> ParsedCV:
    return parse_text(extract_text(data, filename))
