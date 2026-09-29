"""Interview question generator.

Baseline: templates chosen by the role, the candidate's skills, and the
job's missing skills, with answer *guides* that point back at the
candidate's own CV lines. Generating full model answers with an LLM
(grounded only in the CV) is task IQ-2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .cv_parser import parse_text
from .resume_scorer import ACTION_VERBS, METRIC_RE
from .skill_matcher import match
from .skills import category_of


@dataclass
class Question:
    category: str  # behavioural | technical | experience | gap
    question: str
    answer_guide: str

    def to_dict(self) -> dict:
        return asdict(self)


BEHAVIOURAL = [
    Question(
        "behavioural",
        "Tell me about a time you disagreed with a technical decision. What did you do?",
        "Use STAR: the Situation, your Task, the Actions you took to make your case with evidence, and the Result, including what you learned.",
    ),
    Question(
        "behavioural",
        "Describe a project that failed or slipped. What would you do differently?",
        "Own your part, be specific about the root cause, and end with a concrete change you've since made to how you work.",
    ),
    Question(
        "behavioural",
        "How do you explain a model's limitations to a non-technical stakeholder?",
        "Pick a real example. Show you translate metrics into business risk and suggest mitigations, not just caveats.",
    ),
]

TECHNICAL_BY_CATEGORY = {
    "ai": "How have you evaluated {skill} systems in practice? Which metrics did you use and why?",
    "framework": "What's a non-obvious pitfall you've hit with {skill}, and how did you work around it?",
    "language": "What {skill} feature or idiom do you rely on most, and when would you avoid it?",
    "tooling": "Walk me through how you've used {skill} in a production workflow.",
    "soft": "Give an example that shows your {skill} made a measurable difference to a team outcome.",
}


def _experience_questions(experience: list[str], limit: int) -> list[Question]:
    # Only achievement bullets (not job-title lines), preferring ones with
    # numbers: they make the best "tell me more" prompts.
    bullets = [b for b in experience if b.split() and b.split()[0].lower().strip(",.") in ACTION_VERBS]
    ranked = sorted(bullets, key=lambda b: bool(METRIC_RE.search(b)), reverse=True)
    return [
        Question(
            "experience",
            f'Your CV says: "{bullet}". Walk me through how you did that.',
            "Explain the starting point, the approach you chose over alternatives, your personal contribution, and how the result was measured.",
        )
        for bullet in ranked[:limit]
        if len(bullet.split()) >= 5
    ]


def generate(
    role: str,
    cv_text: str | None = None,
    job_description: str | None = None,
    limit: int = 10,
) -> list[Question]:
    questions: list[Question] = [
        Question(
            "behavioural",
            f"Why this {role} role, and why now?",
            "Connect two or three specific things about the role to evidence from your background. Avoid generic enthusiasm.",
        )
    ]

    cv = parse_text(cv_text) if cv_text else None
    if cv:
        questions += _experience_questions(cv.experience, limit=3)

    if cv_text and job_description:
        result = match(cv_text, job_description)
        for skill in result.missing_required[:2]:
            questions.append(
                Question(
                    "gap",
                    f"This role needs {skill}, which isn't on your CV. How would you get productive with it?",
                    "Be honest about the gap. Point to the closest thing you have done and give a concrete ramp-up plan.",
                )
            )
        skills = result.matched
    else:
        skills = cv.skills if cv else []

    for skill in skills[:4]:
        template = TECHNICAL_BY_CATEGORY.get(category_of(skill) or "", TECHNICAL_BY_CATEGORY["tooling"])
        questions.append(
            Question(
                "technical",
                template.format(skill=skill),
                f"Anchor your answer in a specific project where you used {skill}. Interviewers probe for depth, not breadth.",
            )
        )

    questions += BEHAVIOURAL
    return questions[:limit]
