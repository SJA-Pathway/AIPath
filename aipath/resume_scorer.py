"""Resume scorer: ATS-style score with explainable, actionable feedback.

Every point awarded comes from a named check with a message, so a candidate
can always see *why* they got a score. Weights are a first guess; calibrating
them against real recruiter judgements is task RS-3.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .cv_parser import ParsedCV, parse_text
from .skill_matcher import match

ACTION_VERBS = {
    "achieved", "automated", "built", "created", "cut", "delivered", "deployed",
    "designed", "developed", "drove", "grew", "implemented", "improved",
    "increased", "launched", "led", "managed", "mentored", "migrated",
    "optimised", "optimized", "owned", "reduced", "refactored", "scaled",
    "shipped", "trained",
}
METRIC_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|x\b|k\b|m\b|ms\b|users|customers|hours|days)|[$£€₹]\s?\d", re.IGNORECASE)
CORE_SECTIONS = ("experience", "education", "skills")


@dataclass
class Check:
    name: str
    points: int
    max_points: int
    feedback: str


@dataclass
class ScoreResult:
    score: int
    checks: list[Check] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _bullets(cv: ParsedCV) -> list[str]:
    return cv.sections.get("experience", []) + cv.sections.get("projects", [])


def _contact(cv: ParsedCV) -> Check:
    have = [label for label, value in (("email", cv.email), ("phone", cv.phone)) if value]
    points = 10 if len(have) == 2 else 5 if have else 0
    feedback = (
        "Email and phone are both present."
        if points == 10
        else f"Add your {'phone number' if 'email' in have else 'email address'}: recruiters and ATS filters look for both."
        if have
        else "No email or phone found. Put both at the top of the CV."
    )
    return Check("Contact details", points, 10, feedback)


def _sections(cv: ParsedCV) -> Check:
    missing = [s for s in CORE_SECTIONS if s not in cv.sections]
    points = round(20 * (len(CORE_SECTIONS) - len(missing)) / len(CORE_SECTIONS))
    feedback = (
        "Experience, Education and Skills sections are all clearly headed."
        if not missing
        else f"Add clearly labelled section(s): {', '.join(m.title() for m in missing)}. ATS parsers rely on standard headings."
    )
    return Check("Standard sections", points, 20, feedback)


def _length(cv: ParsedCV) -> Check:
    words = cv.word_count
    if 300 <= words <= 900:
        return Check("Length", 10, 10, f"{words} words: a good length for one to two pages.")
    if words < 300:
        return Check("Length", 4 if words >= 150 else 0, 10, f"Only {words} words. Expand your experience with concrete outcomes.")
    return Check("Length", 5, 10, f"{words} words is long. Trim older or less relevant roles to stay under ~900.")


def _action_verbs(cv: ParsedCV) -> Check:
    bullets = _bullets(cv)
    if not bullets:
        return Check("Action verbs", 0, 15, "No experience or project bullets found to evaluate.")
    strong = sum(1 for b in bullets if b.split() and b.split()[0].lower().strip(",.") in ACTION_VERBS)
    ratio = strong / len(bullets)
    points = round(15 * min(ratio / 0.6, 1))
    feedback = (
        f"{strong}/{len(bullets)} bullets start with a strong action verb."
        if ratio >= 0.6
        else f"Only {strong}/{len(bullets)} bullets start with an action verb. Lead with verbs like 'Built', 'Reduced', 'Shipped'."
    )
    return Check("Action verbs", points, 15, feedback)


def _metrics(cv: ParsedCV) -> Check:
    bullets = _bullets(cv)
    if not bullets:
        return Check("Quantified impact", 0, 20, "No experience or project bullets found to evaluate.")
    quantified = sum(1 for b in bullets if METRIC_RE.search(b))
    ratio = quantified / len(bullets)
    points = round(20 * min(ratio / 0.5, 1))
    feedback = (
        f"{quantified}/{len(bullets)} bullets include a number. Good, measurable impact."
        if ratio >= 0.5
        else f"Only {quantified}/{len(bullets)} bullets include a metric. Add numbers (%, users, time saved, revenue)."
    )
    return Check("Quantified impact", points, 20, feedback)


def _skills(cv: ParsedCV, cv_text: str, job_description: str | None) -> Check:
    if job_description:
        result = match(cv_text, job_description)
        points = round(25 * result.score / 100)
        missing = result.missing_required[:5]
        feedback = f"Covers {result.score}% of the job's skills." + (
            f" Missing required: {', '.join(missing)}." if missing else ""
        )
        return Check("Job keyword match", points, 25, feedback)
    n = len(cv.skills)
    points = round(25 * min(n / 10, 1))
    feedback = (
        f"{n} recognised skills listed."
        if n >= 10
        else f"Only {n} recognised skills found. List your tools and technologies explicitly (and paste a job description for a targeted score)."
    )
    return Check("Skills coverage", points, 25, feedback)


def score(cv_text: str, job_description: str | None = None) -> ScoreResult:
    cv = parse_text(cv_text)
    checks = [
        _contact(cv),
        _sections(cv),
        _length(cv),
        _action_verbs(cv),
        _metrics(cv),
        _skills(cv, cv_text, job_description),
    ]
    total = sum(c.points for c in checks)
    maximum = sum(c.max_points for c in checks)
    return ScoreResult(score=round(100 * total / maximum), checks=checks)
