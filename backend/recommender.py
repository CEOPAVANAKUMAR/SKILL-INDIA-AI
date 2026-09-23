"""
recommender.py
Skill Intelligence Engine + Recommendation Engine — Modules 2-7

All logic here is deterministic and explainable (weighted overlap scoring),
which is a deliberate choice for a v1: it's fast, needs no training data,
and every score can be traced back to which skills matched or were missing.
The natural next upgrade (see README) is to swap the scoring functions for
embedding-similarity search against a vector database once you have real
resume/job datasets loaded.
"""
import math
import re
from typing import Dict, Iterable, List, Optional, Tuple


def _find_longest_match(text: str, candidates: List[Tuple[str, str]]) -> Optional[str]:
    """
    Search `text` for the longest whole-word/phrase match among
    (search_string, key) candidates, using word-boundary regex so short
    strings (e.g. the skill "R") can't match as a substring of an unrelated
    word (e.g. inside "RAG"). Returns the key of the longest match, or None.
    """
    best_key, best_len = None, -1
    for phrase, key in candidates:
        phrase = phrase.strip()
        if not phrase:
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.IGNORECASE)
        if len(phrase) > best_len and pattern.search(text):
            best_key, best_len = key, len(phrase)
    return best_key


def normalize_skills(raw_skills: Iterable[str], skills_db: dict) -> List[str]:
    """
    Map a list of free-text or canonical skill strings onto canonical skill
    keys. Accepts values that are already canonical keys (e.g. "machine_learning"),
    human labels (e.g. "Machine Learning"), or any known alias.
    """
    label_to_key = {v["label"].lower(): k for k, v in skills_db["skills"].items()}
    alias_to_key = {}
    for key, meta in skills_db["skills"].items():
        for alias in meta["aliases"]:
            alias_to_key[alias.lower()] = key

    normalized = set()
    for raw in raw_skills:
        if not raw:
            continue
        candidate = raw.strip().lower()
        if candidate in skills_db["skills"]:
            normalized.add(candidate)
        elif candidate in label_to_key:
            normalized.add(label_to_key[candidate])
        elif candidate in alias_to_key:
            normalized.add(alias_to_key[candidate])
    return sorted(normalized)


def _label(key: str, skills_db: dict) -> str:
    return skills_db["skills"][key]["label"]


def find_unrecognized(raw_skills: Iterable[str], skills_db: dict) -> List[str]:
    """
    Return the raw input strings that don't map to any known skill key,
    label, or alias.

    This is intentionally separate from normalize_skills(): that function
    only returns the *set* of matched canonical keys, so there's no way to
    tell, after the fact, which raw strings a given key came from (aliases
    normalize to a different label than what the user typed, e.g. "python3"
    -> key "python" / label "Python"). Comparing raw text against only the
    labels of the *matched* keys — the previous approach in this endpoint —
    incorrectly flagged legitimately-recognized aliases as unrecognized.
    """
    label_to_key = {v["label"].lower(): k for k, v in skills_db["skills"].items()}
    alias_to_key = {}
    for key, meta in skills_db["skills"].items():
        for alias in meta["aliases"]:
            alias_to_key[alias.lower()] = key

    unrecognized = []
    for raw in raw_skills:
        candidate = (raw or "").strip()
        if not candidate:
            continue
        low = candidate.lower()
        if low in skills_db["skills"] or low in label_to_key or low in alias_to_key:
            continue
        unrecognized.append(candidate)
    return unrecognized


def skill_gap(user_skills: List[str], career_key: str, skills_db: dict) -> dict:
    """Compare a user's skills against one target career's weighted requirements."""
    career = skills_db["careers"].get(career_key)
    if not career:
        raise KeyError(f"Unknown career: {career_key}")

    required = career["required_skills"]
    user_set = set(user_skills)
    total_weight = sum(required.values())
    matched_weight = sum(w for s, w in required.items() if s in user_set)

    current_score = round((matched_weight / total_weight) * 100) if total_weight else 0
    matched = [{"skill": s, "label": _label(s, skills_db), "weight": w}
               for s, w in required.items() if s in user_set]
    missing = [{"skill": s, "label": _label(s, skills_db), "weight": w}
               for s, w in required.items() if s not in user_set]
    missing.sort(key=lambda m: m["weight"], reverse=True)
    matched.sort(key=lambda m: m["weight"], reverse=True)

    return {
        "career": career_key,
        "career_label": career["label"],
        "current_score": current_score,
        "required_score": 100,
        "gap": 100 - current_score,
        "matched_skills": matched,
        "missing_skills": missing,
    }


def rank_careers(user_skills: List[str], skills_db: dict, top_n: int = 9) -> List[dict]:
    """Score every career in the database against the user's skills, best first."""
    results = []
    for career_key, career in skills_db["careers"].items():
        gap = skill_gap(user_skills, career_key, skills_db)
        results.append({
            "career": career_key,
            "career_label": career["label"],
            "description": career["description"],
            "match": gap["current_score"],
            "matched_count": len(gap["matched_skills"]),
            "total_required": len(career["required_skills"]),
            "top_missing": [m["label"] for m in gap["missing_skills"][:4]],
        })
    results.sort(key=lambda r: r["match"], reverse=True)
    return results[:top_n]


def rank_jobs(user_skills: List[str], skills_db: dict, top_n: int = 10) -> List[dict]:
    """Score every sample job posting against the user's skills, best first."""
    user_set = set(user_skills)
    results = []
    for job in skills_db["jobs"]:
        required = set(job["required_skills"])
        matched = required & user_set
        missing = required - user_set
        match_pct = round((len(matched) / len(required)) * 100) if required else 0
        results.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "career": job["career"],
            "match": match_pct,
            "matched_skills": [_label(s, skills_db) for s in sorted(matched)],
            "missing_skills": [_label(s, skills_db) for s in sorted(missing)],
        })
    results.sort(key=lambda r: r["match"], reverse=True)
    return results[:top_n]


def generate_learning_path(
    user_skills: List[str],
    career_key: str,
    skills_db: dict,
    months: int = 6,
) -> dict:
    """
    Build a month-by-month roadmap that closes the skill gap for a target
    career, heaviest / most foundational missing skills first. Each month
    gets 1+ skills, sample courses, and a hands-on project suggestion.
    """
    gap = skill_gap(user_skills, career_key, skills_db)
    missing = gap["missing_skills"]  # already sorted by weight desc

    if not missing:
        return {
            "career": career_key,
            "career_label": gap["career_label"],
            "current_score": gap["current_score"],
            "months": [],
            "message": "No skill gap detected — this profile already meets the target requirements.",
        }

    months = max(1, months)
    per_month = math.ceil(len(missing) / months)
    roadmap = []
    for i in range(0, len(missing), per_month):
        chunk = missing[i:i + per_month]
        month_number = len(roadmap) + 1
        month_skills = []
        for item in chunk:
            skill_key = item["skill"]
            courses = skills_db["courses"].get(skill_key, [])
            project = skills_db["project_ideas"].get(
                skill_key,
                f"Build a small project that applies {item['label']} in a real scenario.",
            )
            month_skills.append({
                "skill": item["label"],
                "courses": courses,
                "project": project,
            })
        roadmap.append({"month": month_number, "focus_skills": month_skills})

    return {
        "career": career_key,
        "career_label": gap["career_label"],
        "current_score": gap["current_score"],
        "months": roadmap,
    }


def resume_tips(raw_text: str) -> List[str]:
    """
    Lightweight, rule-based resume feedback (Module: Resume Improvement AI).
    Looks for common weaknesses rather than rewriting content, since that
    needs an LLM — see chat_reply() for the LLM extension point.
    """
    tips = []
    lower = raw_text.lower()

    if not any(ch.isdigit() for ch in raw_text):
        tips.append(
            "Add measurable outcomes to your bullet points (e.g. \"reduced latency by 30%\", "
            "\"served 10k+ users\") — quantified impact stands out far more than task descriptions."
        )
    if "responsible for" in lower or "worked on" in lower:
        tips.append(
            "Replace passive phrasing like \"responsible for\" / \"worked on\" with strong action "
            "verbs: Built, Designed, Automated, Optimized, Led."
        )
    if len(raw_text) < 800:
        tips.append(
            "Your resume content looks short — consider adding 2-3 projects with a one-line "
            "problem statement, your approach, and the result for each."
        )
    if "project" not in lower:
        tips.append(
            "No projects section detected. For technical roles, 2-3 well-described projects "
            "often matter more than a long skills list."
        )
    if not tips:
        tips.append("Resume looks solid structurally — focus next on tailoring keywords to each job you apply to.")
    return tips


def chat_reply(message: str, user_skills: List[str], skills_db: dict) -> dict:
    """
    Rule-based Career Assistant Chatbot (Module 7). Tries to detect a career
    or skill mentioned in the question and answers with real skill-gap data
    instead of a generic canned response.

    To upgrade this to a true LLM assistant: if ANTHROPIC_API_KEY is set in
    the environment, call the Anthropic Messages API with this same
    skill-gap data as context so the model phrases a natural-language reply
    grounded in real numbers instead of hallucinating requirements. See
    llm_chat.py for a ready-to-use implementation of that call.
    """
    # 1) Does the message name a career we know about? Pick the longest /
    # most specific label match so "Generative AI Engineer" wins over the
    # shorter "AI Engineer" when both appear in the text.
    career_candidates = [(c["label"], key) for key, c in skills_db["careers"].items()]
    matched_career = _find_longest_match(message, career_candidates)

    if matched_career:
        gap = skill_gap(user_skills, matched_career, skills_db)
        if gap["missing_skills"]:
            missing_str = ", ".join(m["label"] for m in gap["missing_skills"][:5])
            reply = (
                f"For {gap['career_label']}, your current fit is {gap['current_score']}%. "
                f"The biggest gaps are: {missing_str}. "
                f"Ask me for a learning roadmap and I'll sequence these into a month-by-month plan."
            )
        else:
            reply = (
                f"Good news — based on your listed skills, you already cover the core "
                f"requirements for {gap['career_label']} ({gap['current_score']}%)."
            )
        return {"reply": reply, "matched_career": matched_career, "source": "rule_based"}

    # 2) Does the message name a specific skill? Match against every known
    # alias (not just the display label) using the same longest-match rule.
    skill_candidates = [
        (alias, key) for key, meta in skills_db["skills"].items() for alias in meta["aliases"]
    ]
    matched_skill = _find_longest_match(message, skill_candidates)
    if matched_skill:
        meta = skills_db["skills"][matched_skill]
        in_profile = matched_skill in user_skills
        courses = skills_db["courses"].get(matched_skill, [])
        course_str = f" A good starting point: {courses[0]['name']} ({courses[0]['platform']})." if courses else ""
        status = "you already have this listed in your profile." if in_profile else "this isn't in your current skill list yet."
        reply = f"{meta['label']} — {status}{course_str}"
        return {"reply": reply, "matched_skill": matched_skill, "source": "rule_based"}

    # 3) Fallback
    careers_list = ", ".join(c["label"] for c in skills_db["careers"].values())
    reply = (
        "I can tell you the skill requirements and your current gap for any of these roles: "
        f"{careers_list}. Try asking, for example, \"what skills do I need for Generative AI Engineer?\""
    )
    return {"reply": reply, "source": "rule_based"}
