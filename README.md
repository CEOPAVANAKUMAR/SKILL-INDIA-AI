# SkillMind AI — NLP Career Intelligence, Learning, Training, Assessment & Job Readiness Platform

> Upload your resume. SkillMind understands where you are, discovers where you
> can go, tells you what you're missing, teaches you what you need, tests
> whether you actually learned it, verifies your progress, and guides you
> from **Scratch → Diamond** until you're ready to target relevant jobs.

This is v2 of the original SkillMind AI college project. It keeps every
original feature (resume parsing, skill normalization, career/job
recommendations, skill-gap analysis, learning-path generation, the chatbot)
working exactly as before, and builds a full learning/training/assessment
platform on top of it, organized into real backend modules with SQLite
persistence.

---

## 1. Project structure

```
skillmind/
├── backend/
│   ├── app.py                     # FastAPI app — wires every route (legacy + new)
│   ├── db.py                      # SQLite persistence layer (profiles, skills, progress, assessments, mastery)
│   ├── recommender.py             # UNCHANGED — skill normalize/gap/rank/learning-path/chat (v1)
│   ├── resume_parser_legacy.py    # UNCHANGED — text extraction + alias-based skill matching (v1)
│   ├── llm_chat.py                # UNCHANGED — optional LLM-backed chat, rule-based fallback
│   ├── nlp/
│   │   ├── text_processing.py     # clean_text, tokenize, section detection, structured extraction
│   │   └── similarity.py          # TF-IDF + cosine similarity (scikit-learn, with pure-Python fallback)
│   ├── resume/
│   │   ├── parser.py              # Module 1 — full NLP resume pipeline (wraps legacy parser)
│   │   └── improve.py             # Module 17 — resume re-analysis / improvement suggestions
│   ├── skills/
│   │   ├── level_estimator.py     # "estimated skill level" from resume evidence
│   │   ├── mastery.py             # Module 13 — SkillMind Estimated Mastery (weighted composite)
│   │   └── gap_priority.py        # Module 6 + 8 — priority tiers, learning order, extra-skills engine
│   ├── careers/discovery.py       # Module 4 — explainable career discovery
│   ├── jobs/matching.py           # Module 5 — job role matching with readiness labels
│   ├── courses/recommend.py       # Module 7 — course/resource recommendation
│   ├── projects/recommend.py      # Module 14 — Beginner → Portfolio project ladder
│   ├── learning/
│   │   ├── roadmap.py             # Module 9 — "Scratch → Diamond" dynamic roadmap
│   │   └── content.py             # Module 10 — Learn-stage lesson content
│   ├── assessment/
│   │   ├── question_bank.py       # Module 11 — curated question bank (10 anchor skills)
│   │   └── engine.py              # Module 11 + 12 — grading + adaptive recommendation
│   ├── readiness/job_readiness.py # Module 15 — "Am I Job Ready?" (6 dimensions)
│   ├── utils/                     # reserved for future cross-cutting helpers (currently unused —
│   │                               # each module keeps its own small helpers for a demo-sized codebase)
│   └── data/
│       ├── skills_database.json   # UNCHANGED — 72 skills, 9 careers, 10 jobs, courses, project ideas
│       └── skillmind.db           # created automatically on first run (SQLite, gitignored)
├── frontend/
│   └── index.html                 # single-file SPA — new premium dashboard, 15 sections
├── sample_resumes/
│   └── sample_resume.txt
├── requirements.txt
└── README.md                      # this file
```

### Files changed from the original v1 ZIP
- `frontend/index.html` — fully rebuilt (premium dashboard, all 15 sections below)
- `requirements.txt` — added `scikit-learn` (for the TF-IDF similarity layer)

### Files unchanged (reused as-is, per "improve rather than replace")
- `backend/recommender.py`, `backend/resume_parser_legacy.py` (renamed from
  `resume_parser.py` only so `resume/parser.py` could take the more
  important `resume` package name — logic is byte-for-byte the same),
  `backend/llm_chat.py`, `backend/data/skills_database.json`,
  `sample_resumes/sample_resume.txt`

### New files
Everything under `backend/nlp/`, `backend/resume/`, `backend/skills/`,
`backend/careers/`, `backend/jobs/`, `backend/courses/`, `backend/projects/`,
`backend/learning/`, `backend/assessment/`, `backend/readiness/`,
`backend/db.py`, and a new `backend/app.py` that wires all of it together
while keeping every original route.

---

## 2. Required packages

```
fastapi==0.115.0
uvicorn==0.30.6
python-multipart==0.0.9
pdfplumber==0.11.4
python-docx==1.1.2
requests==2.32.3
pydantic==2.9.2
scikit-learn==1.5.2
```

Only one new dependency vs. v1: **scikit-learn**, used solely for
`TfidfVectorizer` + `cosine_similarity` (no model download — just the
vectorization/cosine-similarity algorithms). If it's ever missing at
runtime, `nlp/similarity.py` automatically falls back to a pure-Python
term-frequency cosine implementation, so the app never crashes because of
it. SQLite persistence uses Python's built-in `sqlite3` — no extra
dependency, no server to install.

---

## 3. How to run it (Windows CMD)

```cmd
cd skillmind
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn app:app --reload --port 8000
```

Then open **http://localhost:8000** in a browser. (macOS/Linux: same
commands, replace `venv\Scripts\activate` with `source venv/bin/activate`.)

A SQLite file (`backend/data/skillmind.db`) is created automatically on
first run — no setup step needed.

---

## 4. Demo flow (no external APIs required)

1. Open the app → **Dashboard** shows the empty-state journey map.
2. Go to **Resume Analysis** → click **Try Sample Profile** (or upload
   `sample_resumes/sample_resume.txt`, or your own PDF/DOCX/TXT).
3. **My Skills** — see what was auto-detected, add/remove manually.
4. **Career Paths** — 9 careers ranked and explained against your profile.
5. **Skill Gap** — pick a target career (e.g. AI Engineer) → readiness
   gauge, matched/missing skills, Core/Supporting/Differentiator tiers.
6. **Courses** — curated resource per missing skill.
7. **Learning Path** — the Scratch → Diamond roadmap, generated from your
   actual profile (your existing skills show as VERIFIED).
8. **Learn** — pick one of the 10 anchor skills (Python, Git, SQL,
   Statistics, Pandas, NumPy, Machine Learning, Deep Learning, NLP,
   FastAPI) → structured lesson.
9. **Practice** — exercise + mini-project for that skill.
10. **Assessments** — 5-question test (MCQ / predict-output / debugging /
    coding / scenario) → auto-graded, topic-wise breakdown, adaptive
    recommendation (revise / practice more / advance).
11. Skill Mastery and the roadmap update automatically after each test.
12. **Job Readiness** — 6-dimension estimate for your target role.
13. **Jobs** — sample postings ranked and filterable by match tier.
14. **Resume Improvement** — strengths, missing sections, weak project
    lines, missing metrics, and target-career-aware suggestions.
15. **AI Assistant** — the original chatbot, always reachable, LLM-backed
    when configured with a graceful rule-based fallback otherwise.

---

## 5. NLP components — what's actually "NLP" here, and how honestly

| Stage | Technique | Where |
|---|---|---|
| Text extraction | pdfplumber / python-docx | `resume_parser_legacy.py` (unchanged) |
| Text cleaning | whitespace/control-char normalization | `nlp/text_processing.clean_text` |
| Section detection | header pattern matching (regex over short lines) | `nlp/text_processing.split_sections` |
| Tokenization / stopwords | hand-built stopword list, regex tokenizer | `nlp/text_processing.tokenize` |
| Skill / entity extraction | longest-alias-first regex matcher over the 72-skill catalog (deterministic, explainable) | `resume_parser_legacy.extract_skills` (unchanged, reused) |
| Structured extraction | degree/branch/grad-year, GitHub/LinkedIn links, bulleted project/experience/certification items | `nlp/text_processing.py` |
| Skill-level estimation | evidence scoring across sections (projects/experience weighted higher than a bare skills-list mention) | `skills/level_estimator.py` |
| Semantic similarity | TF-IDF vectorization + cosine similarity (scikit-learn) | `nlp/similarity.py`, used in `careers/discovery.py` |
| Career/job matching | weighted keyword-overlap scoring (unchanged `recommender.py`) + semantic similarity as a secondary signal | `careers/discovery.py`, `jobs/matching.py` |
| Course/skill mapping | rule-based mapping from missing skills → curated resources | `courses/recommend.py` |
| Natural-language learning content | hand-authored per-skill lessons (10 skills) + data-grounded template fallback (all 72) | `learning/content.py` |
| Question generation | curated question bank (10 skills × 5 question types), scored automatically | `assessment/question_bank.py`, `assessment/engine.py` |
| Personalized recommendation | adaptive loop (score → revise/practice/advance) + weighted Skill Mastery composite | `assessment/engine.py`, `skills/mastery.py` |

**Deliberately not used:** spaCy models, sentence-transformers, or any
downloaded embedding model. The brief asked to avoid "extremely heavy
infrastructure" and keep the project "runnable locally" — a downloaded
transformer model is a common point of failure in a classroom demo (no
internet, disk space, slow first run). TF-IDF + cosine similarity is a
real, textbook NLP technique that needs zero downloads and is easy to
explain in a viva. Swapping in spaCy's `PhraseMatcher` or a
sentence-transformer for the similarity layer is a contained, drop-in
upgrade — `nlp/similarity.py` is the one place that would change.

---

## 6. What's genuinely new vs. the original project

The original ZIP was a resume analyzer + recommender + chatbot. v2 adds an
entire **second half** of the product the brief asked for:

- **Persistence** — every profile, skill evidence entry, learning-progress
  status, assessment result, and mastery score is now saved to SQLite and
  survives a page reload (via a `profile_id` the frontend keeps in
  `localStorage`). v1 had no database at all.
- **Skill-level estimation** — v1 said "Python = present". v2 estimates
  Beginner/Intermediate/Advanced from *where* in the resume a skill
  appears, with a visible confidence score and evidence list.
- **Explainable career discovery** — every recommended career now says
  *why* ("Your profile already covers 6 of 9 skills this role weighs
  most: Python, Pandas, NumPy...").
- **Priority-tiered skill gap** — missing skills are now Core / Supporting
  / Differentiator (reusing the existing requirement weights, not
  invented data), with an explicit learning order.
- **Scratch → Diamond roadmap** — a genuinely new, dynamic 6-level roadmap
  that marks skills you already have as VERIFIED and only expands what's
  actually missing.
- **Full Learn → Practice → Test loop** — structured lessons, exercises,
  and auto-graded 5-question assessments for 10 anchor skills spanning
  every roadmap level, with topic-wise feedback.
- **Adaptive learning loop** — a low test score routes you back to
  "revise"; a mid score to "practice more"; a high score marks the skill
  VERIFIED and updates the roadmap and mastery score — exactly the
  SQL-42%-vs-91% behavior described in the brief.
- **SkillMind Estimated Mastery** — a transparent, weighted composite of
  resume evidence + learning progress + practice + assessment + project
  evidence, always shown with its component breakdown, never as a bare
  number.
- **Job Readiness (6 dimensions)** — technical / project / assessment /
  portfolio / resume / interview, each traceable to real data, always
  carrying the "estimated, not a guarantee" caveat.
- **Resume Improvement v2** — now checks for missing sections, weak
  (short) project lines, missing quantified metrics, and target-career-
  aware gaps, in addition to the original tips.
- **15-section dashboard** — the full journey (Dashboard → Resume →
  Skills → Career Paths → Skill Gap → Courses → Learning Path → Learn →
  Practice → Assessments → Projects → Job Readiness → Jobs → Resume
  Improvement → AI Assistant), replacing the old flat single-page layout.

---

## 7. Limitations & future improvements (stated honestly, as the brief asks)

- **Question bank depth**: only 10 skills (spanning every roadmap level)
  have curated Learn content and assessments. The other 62 skills in the
  catalog still get a usable, data-grounded guide and course
  recommendation, but not a full lesson/quiz — the UI is explicit about
  which is which (`depth: "full"` vs `"guide"`, `has_assessment` flag).
  Extending the curated set is pure content work, no architecture change.
- **"Coding" questions are multiple-choice**, not a real code judge — the
  brief's five question *styles* are represented, but grading is
  automatic multiple-choice rather than executing submitted code. A real
  sandboxed code-execution judge is future work.
- **Sign-in is optional and intentionally minimal** — email/password only
  (stdlib `hashlib.pbkdf2_hmac` hashing + random bearer session tokens in
  a new `users`/`sessions` SQLite table, see `backend/auth.py`). No email
  verification, password reset, or OAuth. Guests can still use the whole
  app without an account, exactly as in the no-login version — signing in
  just gives your `profile_id` a durable home tied to an account instead
  of only living in one browser's `localStorage`, so the same
  resume/skills/progress can be reached again from any device.
- **Jobs are a local, static, 10-posting dataset**, clearly labeled as
  demo/sample data in every API response — architected so a real job API
  or scraped dataset could be swapped in behind `jobs/matching.py` without
  touching the frontend.
- **Semantic similarity is TF-IDF, not embeddings** — good enough to
  demonstrate the concept and catch some paraphrasing, but won't catch
  deep semantic relationships the way sentence-transformer embeddings
  would. Noted above as a contained future upgrade.
- **Interview readiness** is the weakest-evidence dimension in Job
  Readiness (there's no interview data in a resume) — it's explicitly
  labeled as a proxy derived from the other dimensions, not measured
  directly.
- **Skill-level estimation is resume-text heuristics**, not verified
  expertise — the app is careful to call it "estimated" everywhere and
  folds in real assessment results (once taken) as a much more heavily
  weighted signal in the final Mastery score.

---

## 8. API reference (all endpoints)

**Preserved from v1 (unchanged behavior):**
`GET /api/skills`, `GET /api/careers`, `POST /api/resume/upload` (now also
persists + returns level/evidence), `POST /api/skills/normalize`,
`POST /api/analyze/skill-gap`, `POST /api/analyze/career-recommendations`,
`POST /api/analyze/job-recommendations`, `POST /api/analyze/learning-path`,
`POST /api/chat`, `GET /api/health`

**Sign-in (new, optional):**
`POST /api/auth/signup` `{email, password, name?}` → `{token, user}`,
`POST /api/auth/login` `{email, password}` → `{token, user}`,
`POST /api/auth/logout` (send `Authorization: Bearer <token>`),
`GET /api/auth/me` (send `Authorization: Bearer <token>`) → `{user}`.
`user` is `{id, email, name, profile_id}` — the frontend swaps
`state.profileId` to that `profile_id` on sign-in, so every existing
endpoint below keeps working unchanged for signed-in users too.

**New in v2:**
`GET /api/profile/{id}`, `POST /api/profile/{id}/skills`,
`POST /api/careers/discover`, `POST /api/jobs/match`,
`POST /api/skills/gap`, `POST /api/skills/extra`,
`POST /api/courses/recommend`, `POST /api/projects/recommend`,
`POST /api/roadmap/scratch-to-diamond`,
`GET /api/learning/module/{skill}`, `POST /api/learning/progress`,
`GET /api/learning/available-skills`,
`GET /api/assessment/{skill}`, `POST /api/assessment/{skill}/submit`,
`GET /api/mastery/{profile_id}`, `POST /api/readiness/job`,
`POST /api/resume/reanalyze`
