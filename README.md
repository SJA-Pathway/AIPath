# AIPath

**Open-source AI tooling for careers: CV parsing, resume scoring, skill matching and interview question generation.**

AIPath is an open-source project by [SJA Pathway](https://sjapathway.com) for the **AI/ML Engineering** track. It is built in the open by the community — contribute, learn, and build real, portfolio-worthy work.

**Live demo and task board: [aipath.sjapathway.com](https://aipath.sjapathway.com)**

## What's in here

- **CV parser** — turn a PDF/DOCX resume into structured JSON (contact, experience, education, skills).
- **Resume scorer** — ATS-style scoring with actionable, explainable feedback.
- **Skill matcher** — compare a job description against a CV and surface matched vs missing skills.
- **Interview question generator** — role-aware question sets with model answers grounded in the candidate's real experience.

## Tech stack

Python, FastAPI, scikit-learn, spaCy/transformers, plus TypeScript clients.

## Who can contribute

Open source contribution is **free and open to everyone**, but this track is aimed at people with **2–3 years of professional experience** in AI/ML Engineering, because the work is real and largely self-directed.

> **Please note:** open-source contribution gives you **experience, references from your commit history, and portfolio material** — but it does **not** include a certificate or a reference letter. Those come with the paid [internship plans](https://sjapathway.com/#pricing), which include mentorship, structured tasks, and live company projects.

## Getting started

```bash
git clone https://github.com/SJA-Pathway/AIPath.git
cd AIPath
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                            # run the tests
uvicorn aipath.api:app --reload   # API docs at http://127.0.0.1:8000/docs
```

Or use it as a library:

```python
from aipath import parse_text, score_resume, match_skills, generate_questions

match_skills(cv_text, job_description).missing_required
score_resume(cv_text, job_description).checks        # each check has points + feedback
generate_questions("ML Engineer", cv_text, job_description)
```

1. Pick an open task on the [task board](https://aipath.sjapathway.com/#tasks). Good first issues are a gentle start.
2. Click **Claim on GitHub** to open an issue titled with the task id, so nobody duplicates your work.
3. Fork, branch (`feat/<task-id>-short-name`), commit, and open a PR.
4. Mark the task `"status": "done"` in [`tasks.json`](tasks.json) in the same PR.
5. Join the [Discord](https://discord.gg/qqE5EqXfdy) and say hello in the **AIPath** channel.

## Project layout

| Path | What it is |
|---|---|
| `aipath/cv_parser.py` | CV parser: contact details, sections and skills from text, PDF or DOCX |
| `aipath/resume_scorer.py` | Explainable 0–100 score made of named checks |
| `aipath/skill_matcher.py` | Required vs nice-to-have skill coverage against a job description |
| `aipath/interview.py` | CV-grounded interview questions with answer guides |
| `aipath/skills.py`, `aipath/data/skills.json` | Skill taxonomy and extraction, shared with the site |
| `aipath/api.py` | FastAPI service |
| `tasks.json` | The task board: source of truth for what to work on |
| `site/` | The live site (static, Cloudflare Workers). `public/js/engine.js` is a browser port of the Python engine |

The core package has **no required dependencies**. Install extras as needed: `api` (FastAPI), `docs` (PDF/DOCX reading), `dev` (everything plus tests).

## The live site

`site/` serves the demo and task board at [aipath.sjapathway.com](https://aipath.sjapathway.com). The build copies `tasks.json` and `aipath/data/skills.json` into the site, so the board always matches the repo.

```bash
cd site
npm install
npm run dev      # local preview
npm run deploy   # maintainers only: deploys to Cloudflare
```

The demo runs a JavaScript port of the engine in the browser. If you change the Python behaviour, update `site/public/js/engine.js` to match (automated parity tests are task WEB-2).

## Contributing

- One PR per logical change; keep it reviewable.
- Write a clear description of *why*, not just *what*.
- Match the existing code style; add tests where they make sense.
- Be kind in reviews. Everyone here is learning.

## Community & links

| | |
|---|---|
| Discord | [https://discord.gg/qqE5EqXfdy](https://discord.gg/qqE5EqXfdy) |
| Website | [sjapathway.com](https://sjapathway.com) |
| All repos | [github.com/SJA-Pathway](https://github.com/SJA-Pathway) |
| Contact | ceo@sjapathway.com |

## License

MIT — see [LICENSE](LICENSE).
