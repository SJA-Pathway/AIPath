import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from aipath.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_parse_and_match(cv_text, jd_text):
    parsed = client.post("/parse", json={"cv_text": cv_text}).json()
    assert parsed["email"] == "priya.sharma@example.com"

    matched = client.post("/match", json={"cv_text": cv_text, "job_description": jd_text}).json()
    assert "Kubernetes" in matched["missing_required"]


def test_parse_file_txt(cv_text):
    res = client.post("/parse/file", files={"file": ("cv.txt", cv_text.encode(), "text/plain")})
    assert res.status_code == 200
    assert "PyTorch" in res.json()["skills"]


def test_parse_file_rejects_unknown_type():
    res = client.post("/parse/file", files={"file": ("cv.xyz", b"hi", "application/octet-stream")})
    assert res.status_code == 415


def test_score_and_interview(cv_text):
    assert "score" in client.post("/score", json={"cv_text": cv_text}).json()
    qs = client.post("/interview", json={"role": "ML Engineer", "cv_text": cv_text}).json()["questions"]
    assert qs
