"""AIPath: open-source AI tooling for careers."""

from .cv_parser import ParsedCV, parse_file, parse_text
from .interview import generate as generate_questions
from .resume_scorer import score as score_resume
from .skill_matcher import match as match_skills
from .skills import extract_skills

__version__ = "0.1.0"

__all__ = [
    "ParsedCV",
    "extract_skills",
    "generate_questions",
    "match_skills",
    "parse_file",
    "parse_text",
    "score_resume",
]
