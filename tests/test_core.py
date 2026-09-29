from aipath import extract_skills, generate_questions, match_skills, parse_text, score_resume


def test_extract_skills_uses_aliases_and_word_boundaries():
    skills = extract_skills("Worked with sklearn, k8s and JavaScript; some C++ too.")
    assert "scikit-learn" in skills
    assert "Kubernetes" in skills
    assert "C++" in skills
    assert "Java" not in skills  # must not match inside "JavaScript"


def test_short_terms_need_capitals():
    assert "Go" not in extract_skills("I go to the office and ml is fun")
    assert "Machine Learning" not in extract_skills("ml is fun")
    assert "Machine Learning" in extract_skills("5 years of ML")


def test_parse_contact_sections_and_skills(cv_text):
    cv = parse_text(cv_text)
    assert cv.name == "Priya Sharma"
    assert cv.email == "priya.sharma@example.com"
    assert cv.phone and cv.phone.startswith("+91")
    assert any("github.com" in link for link in cv.links)
    assert {"summary", "experience", "education", "skills"} <= cv.sections.keys()
    assert len(cv.experience) == 5
    assert "PyTorch" in cv.skills


def test_match_splits_required_and_optional(cv_text, jd_text):
    result = match_skills(cv_text, jd_text)
    assert "Kubernetes" in result.missing_required
    assert "LLMs" in result.missing_required
    assert "LangChain" in result.missing_optional
    assert "AWS" in result.matched
    assert 0 < result.score < 100


def test_score_is_explainable(cv_text):
    result = score_resume(cv_text)
    assert 0 <= result.score <= 100
    assert all(c.feedback for c in result.checks)
    assert sum(c.max_points for c in result.checks) == 100


def test_score_with_job_description_mentions_gaps(cv_text, jd_text):
    result = score_resume(cv_text, jd_text)
    keyword = next(c for c in result.checks if c.name == "Job keyword match")
    assert "Kubernetes" in keyword.feedback


def test_interview_questions_are_grounded(cv_text, jd_text):
    questions = generate_questions("NLP Engineer", cv_text, jd_text, limit=12)
    categories = {q.category for q in questions}
    assert {"behavioural", "experience", "gap", "technical"} <= categories
    assert any("18%" in q.question for q in questions)
    assert len(questions) <= 12
