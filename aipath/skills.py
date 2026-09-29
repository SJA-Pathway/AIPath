"""Skill taxonomy and keyword-based skill extraction.

This is the deliberately simple baseline: whole-word alias matching against
``data/skills.json``. Smarter extraction (spaCy NER, embeddings) is tracked
as tasks SM-2 and SM-3 on the live site.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

# Characters that count as part of a "word" when checking boundaries, so that
# "C++" doesn't match inside "C++20" and "Java" doesn't match "JavaScript".
_WORD = r"[\w+#]"


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    terms: tuple[str, ...]  # canonical name + aliases


@lru_cache(maxsize=1)
def load_taxonomy() -> tuple[Skill, ...]:
    raw = resources.files("aipath").joinpath("data/skills.json").read_text("utf-8")
    data = json.loads(raw)["skills"]
    return tuple(
        Skill(name=name, category=info["category"], terms=(name, *info.get("aliases", [])))
        for name, info in data.items()
    )


def _term_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!{_WORD}){re.escape(term)}(?!{_WORD})", re.IGNORECASE)


@lru_cache(maxsize=1)
def _compiled() -> tuple[tuple[Skill, tuple[tuple[str, re.Pattern[str]], ...]], ...]:
    return tuple(
        (skill, tuple((term, _term_pattern(term)) for term in skill.terms))
        for skill in load_taxonomy()
    )


def _short_term_ok(term: str, found: str, canonical: str) -> bool:
    # Terms of 1-2 chars ("R", "Go", "ML", "ts") collide with ordinary words,
    # so only accept them written in capitals or exactly as the canonical name.
    if len(term) > 2:
        return True
    return found.isupper() or found == canonical


def extract_skills(text: str) -> list[str]:
    """Return canonical skill names mentioned in ``text``, in taxonomy order."""
    found: list[str] = []
    for skill, patterns in _compiled():
        for term, pattern in patterns:
            if any(_short_term_ok(term, m.group(0), skill.name) for m in pattern.finditer(text)):
                found.append(skill.name)
                break
    return found


def category_of(skill_name: str) -> str | None:
    for skill in load_taxonomy():
        if skill.name == skill_name:
            return skill.category
    return None
