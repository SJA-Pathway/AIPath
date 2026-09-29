"""Skill matcher: compare a job description against a CV.

Skills listed under a "nice to have" / "preferred" / "bonus" heading in the
job description count half as much as required ones. Semantic matching
(e.g. "PyTorch" partially satisfying "deep learning frameworks") is task SM-3.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .skills import extract_skills

OPTIONAL_MARKERS = re.compile(
    r"nice[\s-]to[\s-]have|preferred|bonus|plus|desirable|good to have", re.IGNORECASE
)
REQUIRED_MARKERS = re.compile(
    r"requirements|required|must[\s-]have|qualifications|you have|what you.?ll need", re.IGNORECASE
)
OPTIONAL_WEIGHT = 0.5


@dataclass
class MatchResult:
    score: int  # 0-100, weighted coverage of the job's skills
    matched: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)  # in the CV, not asked for

    def to_dict(self) -> dict:
        return asdict(self)


def split_job_skills(job_description: str) -> tuple[list[str], list[str]]:
    """Return (required, optional) skills from a job description."""
    required: list[str] = []
    optional: list[str] = []
    in_optional = False
    for line in job_description.splitlines():
        # A short line naming a section switches mode; long lines are content.
        if len(line.split()) <= 6:
            if OPTIONAL_MARKERS.search(line):
                in_optional = True
            elif REQUIRED_MARKERS.search(line):
                in_optional = False
        target = optional if in_optional else required
        for skill in extract_skills(line):
            if skill not in required and skill not in optional:
                target.append(skill)
    return required, optional


def match(cv_text: str, job_description: str) -> MatchResult:
    cv_skills = set(extract_skills(cv_text))
    required, optional = split_job_skills(job_description)

    total = len(required) + OPTIONAL_WEIGHT * len(optional)
    earned = sum(1 for s in required if s in cv_skills) + OPTIONAL_WEIGHT * sum(
        1 for s in optional if s in cv_skills
    )
    score = round(100 * earned / total) if total else 0

    wanted = set(required) | set(optional)
    return MatchResult(
        score=score,
        matched=[s for s in required + optional if s in cv_skills],
        missing_required=[s for s in required if s not in cv_skills],
        missing_optional=[s for s in optional if s not in cv_skills],
        extra=sorted(cv_skills - wanted),
    )
