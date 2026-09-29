"""FastAPI service exposing the four AIPath tools.

Run locally:  uvicorn aipath.api:app --reload
Docs:         http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from . import __version__
from .cv_parser import parse_file, parse_text
from .interview import generate
from .resume_scorer import score
from .skill_matcher import match

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = FastAPI(
    title="AIPath",
    version=__version__,
    description="Open-source AI tooling for careers: CV parsing, resume scoring, skill matching and interview question generation.",
)


class CVText(BaseModel):
    cv_text: str = Field(min_length=1)


class ScoreRequest(CVText):
    job_description: str | None = None


class MatchRequest(CVText):
    job_description: str = Field(min_length=1)


class InterviewRequest(BaseModel):
    role: str = Field(min_length=1)
    cv_text: str | None = None
    job_description: str | None = None
    limit: int = Field(default=10, ge=1, le=30)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/parse")
def parse(body: CVText) -> dict:
    return parse_text(body.cv_text).to_dict()


@app.post("/parse/file")
async def parse_upload(file: Annotated[UploadFile, File()]) -> dict:
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File larger than 5 MB")
    try:
        return parse_file(data, file.filename or "upload.txt").to_dict()
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(415, str(exc)) from exc


@app.post("/score")
def score_cv(body: ScoreRequest) -> dict:
    return score(body.cv_text, body.job_description).to_dict()


@app.post("/match")
def match_cv(body: MatchRequest) -> dict:
    return match(body.cv_text, body.job_description).to_dict()


@app.post("/interview")
def interview(body: InterviewRequest) -> dict:
    questions = generate(body.role, body.cv_text, body.job_description, body.limit)
    return {"questions": [q.to_dict() for q in questions]}
