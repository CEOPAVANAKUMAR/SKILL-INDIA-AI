"""
db.py — SkillMind AI persistence layer

Uses SQLite (Python's stdlib sqlite3 — no server, no extra dependency,
one file on disk) so the whole platform stays "clone and run locally"
per the project brief. No ORM: the schema is small and explicit enough
that raw SQL is easier to audit for a college demo than an ORM layer
would be.

Data model implemented here (mapped onto SQLite tables):
    User            -> users table (optional email/password sign-in — see
                        auth.py). Guests still work exactly as before: the
                        frontend creates a random profile_id per browser and
                        keeps reusing it. Signing in just gives that
                        profile_id a durable home tied to an account instead
                        of only living in one browser's localStorage.
    Session         -> sessions table (bearer tokens for signed-in users)
    ResumeProfile   -> profiles table
    SkillEvidence   -> profile_skills table (one row per skill the profile has,
                        with the evidence + estimated level that produced it)
    LearningProgress-> learning_progress table
    AssessmentResult-> assessment_results table
    SkillMastery    -> skill_mastery table

Skill / Career / Course / Project / Job / Question "catalog" data stays in
data/skills_database.json + data/question_bank.json — those are reference
data, not per-user data, so they don't need a database table.
"""
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "skillmind.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id              TEXT PRIMARY KEY,
    name            TEXT DEFAULT '',
    email           TEXT DEFAULT '',
    phone           TEXT DEFAULT '',
    degree          TEXT DEFAULT '',
    branch          TEXT DEFAULT '',
    grad_year       TEXT DEFAULT '',
    github          TEXT DEFAULT '',
    education_json  TEXT DEFAULT '[]',
    projects_json   TEXT DEFAULT '[]',
    experience_json TEXT DEFAULT '[]',
    certifications_json TEXT DEFAULT '[]',
    resume_text     TEXT DEFAULT '',
    created_at      REAL,
    updated_at      REAL
);

CREATE TABLE IF NOT EXISTS profile_skills (
    profile_id      TEXT NOT NULL,
    skill_key       TEXT NOT NULL,
    source          TEXT DEFAULT 'manual',   -- 'resume' | 'manual' | 'verified'
    estimated_level TEXT DEFAULT 'Beginner',
    confidence      INTEGER DEFAULT 40,
    evidence_json   TEXT DEFAULT '[]',
    added_at        REAL,
    PRIMARY KEY (profile_id, skill_key)
);

CREATE TABLE IF NOT EXISTS learning_progress (
    profile_id      TEXT NOT NULL,
    skill_key       TEXT NOT NULL,
    status          TEXT DEFAULT 'not_started',  -- not_started|learning|practiced|tested|verified
    last_updated    REAL,
    PRIMARY KEY (profile_id, skill_key)
);

CREATE TABLE IF NOT EXISTS assessment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      TEXT NOT NULL,
    skill_key       TEXT NOT NULL,
    score           INTEGER,
    accuracy        REAL,
    topic_breakdown_json TEXT DEFAULT '{}',
    strengths_json  TEXT DEFAULT '[]',
    weaknesses_json TEXT DEFAULT '[]',
    taken_at        REAL
);

CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    name            TEXT DEFAULT '',
    profile_id      TEXT NOT NULL,
    created_at      REAL
);

CREATE TABLE IF NOT EXISTS sessions (
    token           TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    created_at      REAL,
    expires_at      REAL
);

CREATE TABLE IF NOT EXISTS skill_mastery (
    profile_id          TEXT NOT NULL,
    skill_key           TEXT NOT NULL,
    resume_evidence_score REAL DEFAULT 0,
    learning_score       REAL DEFAULT 0,
    practice_score        REAL DEFAULT 0,
    assessment_score      REAL DEFAULT 0,
    project_score          REAL DEFAULT 0,
    estimated_mastery      REAL DEFAULT 0,
    status                  TEXT DEFAULT 'Beginner',
    updated_at              REAL,
    PRIMARY KEY (profile_id, skill_key)
);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def new_profile_id() -> str:
    return uuid.uuid4().hex[:16]


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


# ---------------------------------------------------------------- profiles

def upsert_profile(profile_id: str, fields: Dict[str, Any]) -> None:
    """Create the profile row if missing, else update the given fields."""
    conn = get_conn()
    try:
        now = time.time()
        existing = conn.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        json_fields = ("education_json", "projects_json", "experience_json", "certifications_json")
        clean = dict(fields)
        for jf in json_fields:
            if jf in clean and not isinstance(clean[jf], str):
                clean[jf] = json.dumps(clean[jf])

        if existing is None:
            cols = ["id", "created_at", "updated_at"] + list(clean.keys())
            vals = [profile_id, now, now] + list(clean.values())
            placeholders = ",".join("?" for _ in cols)
            conn.execute(f"INSERT INTO profiles ({','.join(cols)}) VALUES ({placeholders})", vals)
        else:
            if clean:
                set_clause = ",".join(f"{k} = ?" for k in clean.keys())
                conn.execute(
                    f"UPDATE profiles SET {set_clause}, updated_at = ? WHERE id = ?",
                    list(clean.values()) + [now, profile_id],
                )
            else:
                conn.execute("UPDATE profiles SET updated_at = ? WHERE id = ?", (now, profile_id))
        conn.commit()
    finally:
        conn.close()


def get_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not row:
            return None
        d = _row_to_dict(row)
        for jf in ("education_json", "projects_json", "experience_json", "certifications_json"):
            try:
                d[jf.replace("_json", "")] = json.loads(d.pop(jf) or "[]")
            except Exception:
                d[jf.replace("_json", "")] = []
        return d
    finally:
        conn.close()


# ------------------------------------------------------------ profile_skills

def upsert_profile_skill(profile_id: str, skill_key: str, source: str,
                          estimated_level: str, confidence: int, evidence: List[str]) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO profile_skills (profile_id, skill_key, source, estimated_level, confidence, evidence_json, added_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(profile_id, skill_key) DO UPDATE SET
                 source=excluded.source, estimated_level=excluded.estimated_level,
                 confidence=excluded.confidence, evidence_json=excluded.evidence_json""",
            (profile_id, skill_key, source, estimated_level, confidence, json.dumps(evidence), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def mark_skill_verified(profile_id: str, skill_key: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE profile_skills SET source='verified' WHERE profile_id=? AND skill_key=?",
            (profile_id, skill_key),
        )
        conn.commit()
    finally:
        conn.close()


def get_profile_skills(profile_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM profile_skills WHERE profile_id = ?", (profile_id,)).fetchall()
        out = []
        for r in rows:
            d = _row_to_dict(r)
            try:
                d["evidence"] = json.loads(d.pop("evidence_json") or "[]")
            except Exception:
                d["evidence"] = []
            out.append(d)
        return out
    finally:
        conn.close()


# --------------------------------------------------------- learning_progress

def set_learning_status(profile_id: str, skill_key: str, status: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO learning_progress (profile_id, skill_key, status, last_updated)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(profile_id, skill_key) DO UPDATE SET status=excluded.status, last_updated=excluded.last_updated""",
            (profile_id, skill_key, status, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def get_learning_progress(profile_id: str) -> Dict[str, str]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT skill_key, status FROM learning_progress WHERE profile_id = ?", (profile_id,)).fetchall()
        return {r["skill_key"]: r["status"] for r in rows}
    finally:
        conn.close()


# ------------------------------------------------------- assessment_results

def save_assessment_result(profile_id: str, skill_key: str, score: int, accuracy: float,
                            topic_breakdown: Dict[str, Any], strengths: List[str], weaknesses: List[str]) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO assessment_results
               (profile_id, skill_key, score, accuracy, topic_breakdown_json, strengths_json, weaknesses_json, taken_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (profile_id, skill_key, score, accuracy, json.dumps(topic_breakdown),
             json.dumps(strengths), json.dumps(weaknesses), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def latest_assessment(profile_id: str, skill_key: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT * FROM assessment_results WHERE profile_id=? AND skill_key=?
               ORDER BY taken_at DESC LIMIT 1""",
            (profile_id, skill_key),
        ).fetchone()
        if not row:
            return None
        d = _row_to_dict(row)
        d["topic_breakdown"] = json.loads(d.pop("topic_breakdown_json") or "{}")
        d["strengths"] = json.loads(d.pop("strengths_json") or "[]")
        d["weaknesses"] = json.loads(d.pop("weaknesses_json") or "[]")
        return d
    finally:
        conn.close()


def all_assessments(profile_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT profile_id, skill_key, score, accuracy, taken_at FROM assessment_results WHERE profile_id=? ORDER BY taken_at DESC",
            (profile_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ------------------------------------------------------------ skill_mastery

def upsert_mastery(profile_id: str, skill_key: str, resume_evidence_score: float, learning_score: float,
                    practice_score: float, assessment_score: float, project_score: float,
                    estimated_mastery: float, status: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO skill_mastery
               (profile_id, skill_key, resume_evidence_score, learning_score, practice_score,
                assessment_score, project_score, estimated_mastery, status, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(profile_id, skill_key) DO UPDATE SET
                 resume_evidence_score=excluded.resume_evidence_score,
                 learning_score=excluded.learning_score,
                 practice_score=excluded.practice_score,
                 assessment_score=excluded.assessment_score,
                 project_score=excluded.project_score,
                 estimated_mastery=excluded.estimated_mastery,
                 status=excluded.status,
                 updated_at=excluded.updated_at""",
            (profile_id, skill_key, resume_evidence_score, learning_score, practice_score,
             assessment_score, project_score, estimated_mastery, status, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def get_mastery(profile_id: str, skill_key: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM skill_mastery WHERE profile_id=? AND skill_key=?", (profile_id, skill_key)
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_all_mastery(profile_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM skill_mastery WHERE profile_id=?", (profile_id,)).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ------------------------------------------------------------------- users
# Sign-in support: an account is just a durable pointer to a profile_id, so
# logging in on any browser restores the same resume/skills/progress that
# were previously reachable only via localStorage.

def create_user(user_id: str, email: str, password_hash: str, name: str, profile_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, name, profile_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email.strip().lower(), password_hash, name, profile_id, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------- sessions

def create_session(token: str, user_id: str, ttl_seconds: float = 60 * 60 * 24 * 30) -> None:
    conn = get_conn()
    try:
        now = time.time()
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, now + ttl_seconds),
        )
        conn.commit()
    finally:
        conn.close()


def get_session_user(token: str) -> Optional[Dict[str, Any]]:
    """Returns the user row for a valid, unexpired session token, else None."""
    if not token:
        return None
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT s.user_id, s.expires_at FROM sessions s WHERE s.token = ?", (token,)
        ).fetchone()
        if not row:
            return None
        if row["expires_at"] and row["expires_at"] < time.time():
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (row["user_id"],)).fetchone()
        return _row_to_dict(user_row) if user_row else None
    finally:
        conn.close()


def delete_session(token: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()
