"""
app.py — SkillMind AI backend (v2: NLP Career Intelligence, Learning,
Training, Assessment and Job Readiness Platform)

Run with:
    uvicorn app:app --reload --port 8000

Then open http://localhost:8000 in your browser.

This file preserves every original endpoint (skills, careers, resume
upload, normalize, skill-gap, career/job recommendations, learning-path,
chat, health) unchanged in behavior, and adds the new modular engines as
additional routes. See README.md for the full endpoint list and the new
project structure.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Header, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))  # allow `import nlp.x`, `import skills.x`, etc. as top-level packages

import auth
import llm_chat
import recommender
import resume_parser_legacy  # noqa: F401  (kept importable for compatibility)
import db
from nlp import text_processing as tp
from resume.parser import parse_resume_full
from resume.improve import analyze_resume
from skills.gap_priority import gap_with_priority
from skills.mastery import compute_mastery, learning_progress_to_score
from careers.discovery import discover_careers
from jobs.matching import match_jobs
from courses.recommend import recommend_courses_for_gap
from projects.recommend import recommend_projects_for_gap
from learning.roadmap import build_roadmap
from learning.content import get_learning_module, AVAILABLE_FULL_CONTENT_SKILLS
from assessment.engine import build_assessment, grade_submission
from assessment.question_bank import has_assessment, AVAILABLE_ASSESSMENT_SKILLS
from readiness.job_readiness import compute_job_readiness

DATA_PATH = BASE_DIR / "data" / "skills_database.json"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    SKILLS_DB = json.load(f)

db.init_db()

app = FastAPI(title="SkillMind AI — Career Intelligence, Learning & Job Readiness Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# Request / response models
# ================================================================

class SkillsPayload(BaseModel):
    skills: List[str]


class SkillGapPayload(BaseModel):
    skills: List[str]
    career: str


class LearningPathPayload(BaseModel):
    skills: List[str]
    career: str
    months: int = 6


class ChatPayload(BaseModel):
    message: str
    skills: List[str] = []


class ProfileSkillsPayload(BaseModel):
    skills: List[str]


class AssessmentSubmitPayload(BaseModel):
    profile_id: Optional[str] = None
    answers: Dict[str, int]


class LearningProgressPayload(BaseModel):
    profile_id: str
    skill_key: str
    status: str  # not_started | learning | practiced | tested | verified


class ReadinessPayload(BaseModel):
    skills: List[str]
    career: str
    profile_id: Optional[str] = None


class ReanalyzePayload(BaseModel):
    profile_id: str
    target_career: Optional[str] = None


class SignupPayload(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginPayload(BaseModel):
    email: str
    password: str


# ================================================================
# Static reference data (unchanged from v1)
# ================================================================

@app.get("/api/skills")
def list_skills():
    by_category = {}
    for key, meta in SKILLS_DB["skills"].items():
        by_category.setdefault(meta["category"], []).append({"key": key, "label": meta["label"]})
    for cat in by_category:
        by_category[cat].sort(key=lambda s: s["label"])
    return {"categories": by_category}


@app.get("/api/careers")
def list_careers():
    return [
        {"key": k, "label": v["label"], "description": v["description"]}
        for k, v in SKILLS_DB["careers"].items()
    ]


# ================================================================
# NEW — Sign in / Sign up (optional; guest profile_id flow still works)
# ================================================================
# Signing in doesn't replace the existing profile_id model — it just gives
# a profile_id a durable home tied to an email/password instead of only
# living in one browser's localStorage, so the same resume/skills/progress
# can be reached again from any device.

def _user_public(user: Dict) -> Dict:
    return {"id": user["id"], "email": user["email"], "name": user.get("name", ""), "profile_id": user["profile_id"]}


def _current_user(authorization: Optional[str]):
    token = auth.extract_bearer_token(authorization or "")
    return db.get_session_user(token) if token else None


@app.post("/api/auth/signup")
def auth_signup(payload: SignupPayload):
    email = payload.email.strip()
    if not auth.valid_email(email):
        raise HTTPException(400, "Please enter a valid email address.")
    if len(payload.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    if db.get_user_by_email(email):
        raise HTTPException(409, "An account with that email already exists. Try signing in instead.")

    user_id = auth.new_user_id()
    profile_id = db.new_profile_id()
    db.create_user(user_id, email, auth.hash_password(payload.password), payload.name.strip(), profile_id)
    db.upsert_profile(profile_id, {"name": payload.name.strip(), "email": email})

    token = auth.new_token()
    db.create_session(token, user_id)
    user = db.get_user_by_id(user_id)
    return {"token": token, "user": _user_public(user)}


@app.post("/api/auth/login")
def auth_login(payload: LoginPayload):
    email = payload.email.strip()
    user = db.get_user_by_email(email)
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, "Incorrect email or password.")

    token = auth.new_token()
    db.create_session(token, user["id"])
    return {"token": token, "user": _user_public(user)}


@app.post("/api/auth/logout")
def auth_logout(authorization: Optional[str] = Header(None)):
    token = auth.extract_bearer_token(authorization or "")
    if token:
        db.delete_session(token)
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(authorization: Optional[str] = Header(None)):
    user = _current_user(authorization)
    if not user:
        raise HTTPException(401, "Not signed in.")
    return {"user": _user_public(user)}


# ================================================================
# Resume Intelligence Engine (v2: NLP pipeline, section-aware, persisted)
# ================================================================

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), profile_id: Optional[str] = Form(None)):
    allowed = (".pdf", ".docx", ".txt")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(400, f"Unsupported file type. Please upload one of: {', '.join(allowed)}")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "Uploaded file is empty.")

    try:
        profile = parse_resume_full(file_bytes, file.filename, SKILLS_DB)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(422, f"Could not parse resume: {exc}")

    full_text = profile.pop("_raw_text_full", profile.get("raw_text_preview", ""))
    profile["resume_tips"] = recommender.resume_tips(full_text)

    pid = profile_id or db.new_profile_id()
    db.upsert_profile(pid, {
        "name": profile["name"], "email": profile["email"], "phone": profile["phone"],
        "degree": profile["degree"], "branch": profile["branch"], "grad_year": profile["grad_year"],
        "github": profile["github"], "education_json": profile["education"],
        "projects_json": profile["projects"], "experience_json": profile["experience"],
        "certifications_json": profile["certifications"], "resume_text": full_text,
    })
    for skill_key in profile["extracted_skills"]:
        lvl = profile["skill_levels"].get(skill_key, {})
        db.upsert_profile_skill(
            pid, skill_key, source="resume",
            estimated_level=lvl.get("level", "Beginner"),
            confidence=lvl.get("evidence_score", 40),
            evidence=lvl.get("evidence", []),
        )
        db.set_learning_status(pid, skill_key, "learning")

    profile["profile_id"] = pid
    return profile


@app.get("/api/profile/{profile_id}")
def get_profile(profile_id: str):
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(404, "Unknown profile_id.")
    skills = db.get_profile_skills(profile_id)
    progress = db.get_learning_progress(profile_id)
    for s in skills:
        s["label"] = SKILLS_DB["skills"].get(s["skill_key"], {}).get("label", s["skill_key"])
        s["learning_status"] = progress.get(s["skill_key"], "not_started")
    return {"profile": profile, "skills": skills}


@app.post("/api/profile/{profile_id}/skills")
def sync_profile_skills(profile_id: str, payload: ProfileSkillsPayload):
    """Idempotently persist the frontend's current working skill set (manual additions)."""
    normalized = recommender.normalize_skills(payload.skills, SKILLS_DB)
    existing = {s["skill_key"] for s in db.get_profile_skills(profile_id)}
    for key in normalized:
        if key not in existing:
            db.upsert_profile_skill(profile_id, key, source="manual", estimated_level="Beginner",
                                     confidence=35, evidence=["Manually added by user"])
            db.set_learning_status(profile_id, key, "learning")
    return {"profile_id": profile_id, "skills": normalized}


@app.post("/api/skills/normalize")
def normalize_skills(payload: SkillsPayload):
    normalized = recommender.normalize_skills(payload.skills, SKILLS_DB)
    return {
        "skills": normalized,
        "labels": [SKILLS_DB["skills"][s]["label"] for s in normalized],
        "unrecognized": recommender.find_unrecognized(payload.skills, SKILLS_DB),
    }


# ================================================================
# Skill Intelligence + Recommendation Engine — legacy endpoints (unchanged)
# ================================================================

@app.post("/api/analyze/skill-gap")
def analyze_skill_gap(payload: SkillGapPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    return recommender.skill_gap(skills, payload.career, SKILLS_DB)


@app.post("/api/analyze/career-recommendations")
def analyze_career_recommendations(payload: SkillsPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    return recommender.rank_careers(skills, SKILLS_DB)


@app.post("/api/analyze/job-recommendations")
def analyze_job_recommendations(payload: SkillsPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    return recommender.rank_jobs(skills, SKILLS_DB)


@app.post("/api/analyze/learning-path")
def analyze_learning_path(payload: LearningPathPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    return recommender.generate_learning_path(skills, payload.career, SKILLS_DB, payload.months)


# ================================================================
# NEW — Career Discovery Engine (Module 4, explainable)
# ================================================================

@app.post("/api/careers/discover")
def careers_discover(payload: SkillsPayload, profile_id: Optional[str] = None):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    resume_text = None
    if profile_id:
        p = db.get_profile(profile_id)
        resume_text = p["resume_text"] if p else None
    return discover_careers(skills, SKILLS_DB, resume_text=resume_text)


# ================================================================
# NEW — Job Role Matching (Module 5)
# ================================================================

@app.post("/api/jobs/match")
def jobs_match(payload: SkillsPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    return match_jobs(skills, SKILLS_DB)


# ================================================================
# NEW — Skill Gap Engine with priority tiers + Extra Skills Engine (Modules 6, 8)
# ================================================================

@app.post("/api/skills/gap")
def skills_gap(payload: SkillGapPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    return gap_with_priority(skills, payload.career, SKILLS_DB)


@app.post("/api/skills/extra")
def skills_extra(payload: SkillGapPayload):
    """'Extra Skills I Need' — Core / Supporting / Differentiator, with explanation."""
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    gap = gap_with_priority(skills, payload.career, SKILLS_DB)
    return {
        "career": payload.career,
        "career_label": gap["career_label"],
        "extra_skills": gap["extra_skills"],
        "explanation": {
            "core": "Must learn — these are weighted heaviest in this career's requirements.",
            "supporting": "Strongly useful — moderately weighted, commonly requested alongside the core stack.",
            "differentiator": "Lightly weighted, but can make your profile stand out from other applicants.",
        },
    }


# ================================================================
# NEW — Course Recommendation Engine (Module 7)
# ================================================================

@app.post("/api/courses/recommend")
def courses_recommend(payload: SkillGapPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    gap = gap_with_priority(skills, payload.career, SKILLS_DB)
    return recommend_courses_for_gap(gap["missing_skills"], SKILLS_DB, gap["career_label"])


# ================================================================
# NEW — Project Recommendation Engine (Module 14)
# ================================================================

@app.post("/api/projects/recommend")
def projects_recommend(payload: SkillGapPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    gap = gap_with_priority(skills, payload.career, SKILLS_DB)
    missing_keys = [m["skill"] for m in gap["missing_skills"][:8]]
    return recommend_projects_for_gap(missing_keys, SKILLS_DB)


# ================================================================
# NEW — Learning Roadmap: Scratch -> Diamond (Module 9)
# ================================================================

@app.post("/api/roadmap/scratch-to-diamond")
def roadmap_scratch_to_diamond(payload: SkillGapPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")
    return build_roadmap(skills, payload.career, SKILLS_DB)


# ================================================================
# NEW — Learning Module / Training System (Module 10)
# ================================================================

@app.get("/api/learning/module/{skill_key}")
def learning_module(skill_key: str):
    module = get_learning_module(skill_key, SKILLS_DB)
    if not module:
        raise HTTPException(404, f"Unknown skill '{skill_key}'")
    module["has_full_content"] = skill_key in AVAILABLE_FULL_CONTENT_SKILLS
    module["has_assessment"] = has_assessment(skill_key)
    return module


@app.post("/api/learning/progress")
def learning_progress_update(payload: LearningProgressPayload):
    valid = {"not_started", "learning", "practiced", "tested", "verified"}
    if payload.status not in valid:
        raise HTTPException(400, f"status must be one of {sorted(valid)}")
    db.set_learning_status(payload.profile_id, payload.skill_key, payload.status)
    if payload.status == "verified":
        db.mark_skill_verified(payload.profile_id, payload.skill_key)
    _recompute_and_store_mastery(payload.profile_id, payload.skill_key)
    return {"ok": True}


@app.get("/api/learning/available-skills")
def learning_available_skills():
    return {
        "full_content": AVAILABLE_FULL_CONTENT_SKILLS,
        "with_assessment": AVAILABLE_ASSESSMENT_SKILLS,
    }


# ================================================================
# NEW — Skill Assessment Engine + Adaptive Learning Loop (Modules 11, 12, 13)
# ================================================================

@app.get("/api/assessment/{skill_key}")
def assessment_get(skill_key: str):
    if not has_assessment(skill_key):
        raise HTTPException(
            404,
            f"No assessment is available for '{skill_key}' in this demo yet. "
            f"Available: {', '.join(AVAILABLE_ASSESSMENT_SKILLS)}",
        )
    return build_assessment(skill_key)


@app.post("/api/assessment/{skill_key}/submit")
def assessment_submit(skill_key: str, payload: AssessmentSubmitPayload):
    try:
        result = grade_submission(skill_key, payload.answers)
    except ValueError as exc:
        raise HTTPException(404, str(exc))

    if payload.profile_id:
        db.save_assessment_result(
            payload.profile_id, skill_key, result["score"], result["accuracy"],
            result["topic_breakdown"], result["strengths"], result["weaknesses"],
        )
        new_status = "verified" if result["action"] == "advance" else "tested"
        db.set_learning_status(payload.profile_id, skill_key, new_status)
        if new_status == "verified":
            db.mark_skill_verified(payload.profile_id, skill_key)
        _recompute_and_store_mastery(payload.profile_id, skill_key)

    return result


def _recompute_and_store_mastery(profile_id: str, skill_key: str) -> Dict:
    """
    Adaptive loop step: ANALYZE PERFORMANCE -> UPDATE SKILL LEVEL.
    Pulls each mastery component from real stored data (resume evidence
    confidence, learning-progress stage, latest assessment score) and
    writes the combined SkillMind Estimated Mastery back to skill_mastery.
    """
    p_skills = {s["skill_key"]: s for s in db.get_profile_skills(profile_id)}
    resume_evidence = p_skills.get(skill_key, {}).get("confidence", 0)

    progress = db.get_learning_progress(profile_id)
    status = progress.get(skill_key, "not_started")
    learning_score = learning_progress_to_score(status)
    practice_score = learning_score  # this demo doesn't track practice attempts separately from stage

    latest = db.latest_assessment(profile_id, skill_key)
    assessment_score = latest["score"] if latest else 0

    project_score = 100 if status == "verified" else (60 if status in ("tested", "practiced") else 20)

    mastery = compute_mastery(resume_evidence, learning_score, practice_score, assessment_score, project_score)
    db.upsert_mastery(
        profile_id, skill_key,
        mastery["components"]["resume_evidence"], mastery["components"]["learning_progress"],
        mastery["components"]["practice_performance"], mastery["components"]["assessment_performance"],
        mastery["components"]["project_evidence"], mastery["estimated_mastery"], mastery["status"],
    )
    return mastery


@app.get("/api/mastery/{profile_id}")
def mastery_overview(profile_id: str):
    rows = db.get_all_mastery(profile_id)
    for r in rows:
        r["label"] = SKILLS_DB["skills"].get(r["skill_key"], {}).get("label", r["skill_key"])
    return {"profile_id": profile_id, "skills": rows}


# ================================================================
# NEW — Job Readiness Analysis (Module 15)
# ================================================================

@app.post("/api/readiness/job")
def readiness_job(payload: ReadinessPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)
    if payload.career not in SKILLS_DB["careers"]:
        raise HTTPException(404, f"Unknown career '{payload.career}'")

    resume_projects, github, tips, assessment_rows, verified_count = [], "", [], [], 0
    if payload.profile_id:
        p = db.get_profile(payload.profile_id)
        if p:
            resume_projects = p.get("projects", [])
            github = p.get("github", "")
            tips = recommender.resume_tips(p.get("resume_text", "")) if p.get("resume_text") else []
        assessment_rows = db.all_assessments(payload.profile_id)
        progress = db.get_learning_progress(payload.profile_id)
        verified_count = sum(1 for s in progress.values() if s == "verified")

    return compute_job_readiness(
        skills, payload.career, SKILLS_DB, resume_projects=resume_projects, github=github,
        resume_tips=tips, assessment_rows=assessment_rows, verified_project_count=verified_count,
    )


# ================================================================
# NEW — Resume Improvement re-analysis (Module 17)
# ================================================================

@app.post("/api/resume/reanalyze")
def resume_reanalyze(payload: ReanalyzePayload):
    p = db.get_profile(payload.profile_id)
    if not p:
        raise HTTPException(404, "Unknown profile_id.")
    sections = tp.split_sections(p.get("resume_text", ""))
    detected_skills = [s["skill_key"] for s in db.get_profile_skills(payload.profile_id)]
    return analyze_resume(
        p.get("resume_text", ""), sections, p.get("projects", []), detected_skills,
        target_career_key=payload.target_career, skills_db=SKILLS_DB,
    )


# ================================================================
# AI Career Assistant Chatbot (unchanged)
# ================================================================

@app.post("/api/chat")
def chat(payload: ChatPayload):
    skills = recommender.normalize_skills(payload.skills, SKILLS_DB)

    if llm_chat.is_available():
        llm_text = llm_chat.get_llm_reply(payload.message, skills, SKILLS_DB)
        if llm_text:
            return {"reply": llm_text, "source": "llm"}

    return recommender.chat_reply(payload.message, skills, SKILLS_DB)


# ================================================================
# Frontend
# ================================================================

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(404, "Frontend not found.")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "skills_loaded": len(SKILLS_DB["skills"]),
        "careers_loaded": len(SKILLS_DB["careers"]),
        "assessments_available": len(AVAILABLE_ASSESSMENT_SKILLS),
        "full_learning_content_available": len(AVAILABLE_FULL_CONTENT_SKILLS),
    }
