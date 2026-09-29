import pytest

SAMPLE_CV = """Priya Sharma
priya.sharma@example.com | +91 98765 43210 | github.com/priyasharma

Summary
ML engineer with 3 years building NLP systems in Python.

Experience
Machine Learning Engineer, Acme Corp (2022 - present)
- Built a resume-ranking model in PyTorch that improved recruiter shortlist precision by 18%
- Deployed FastAPI inference services on AWS with Docker, cutting latency to 120 ms
- Led a team of 3 to migrate batch pipelines to Airflow
- Responsible for writing documentation

Education
B.Tech Computer Science, IIT Delhi, 2021

Skills
Python, SQL, PyTorch, scikit-learn, NLP, Docker, AWS, Git
"""

SAMPLE_JD = """Senior NLP Engineer

Requirements
- Strong Python and PyTorch
- Experience with NLP and LLMs in production
- Kubernetes and Docker

Nice to have
- LangChain or RAG pipelines
- AWS
"""


@pytest.fixture
def cv_text() -> str:
    return SAMPLE_CV


@pytest.fixture
def jd_text() -> str:
    return SAMPLE_JD
