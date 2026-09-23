"""
learning/roadmap.py — Module 9: "YOUR PATH: SCRATCH -> DIAMOND"

Builds a dynamic 6-level roadmap for a target career from the user's
*actual* profile: skills they already have are marked VERIFIED and shown
(not hidden — the brief explicitly wants "Python -> VERIFIED" visible, not
silently skipped), and only the missing skills required for the target
career are expanded into learning content.

Level assignment is a simple, documented lookup (category default +
explicit overrides for skills that clearly belong at a different stage of
difficulty than their category implies, e.g. `machine_learning` category
"AI & ML" defaults to Silver, but `mlops` in the same category belongs at
Platinum). This keeps the roadmap explainable — every skill's level can be
traced back to one line in LEVEL_OVERRIDES or CATEGORY_DEFAULT_LEVEL below.
"""
from typing import Dict, List

import recommender

LEVELS = [
    {"level": 0, "name": "Scratch", "tagline": "Foundations"},
    {"level": 1, "name": "Iron", "tagline": "Core technical skills"},
    {"level": 2, "name": "Silver", "tagline": "Machine learning"},
    {"level": 3, "name": "Gold", "tagline": "Advanced AI"},
    {"level": 4, "name": "Platinum", "tagline": "Modern AI engineering"},
    {"level": 5, "name": "Diamond", "tagline": "Job-ready capstone"},
]

CATEGORY_DEFAULT_LEVEL = {
    "Programming": 0,
    "Tools": 0,
    "Practices": 1,
    "Databases": 1,
    "ML Libraries": 1,
    "Data Engineering": 3,
    "Web Development": 3,
    "AI & ML": 2,
    "NLP & GenAI": 4,
    "Cloud & DevOps": 4,
}

LEVEL_OVERRIDES = {
    "sql": 1, "r_language": 1, "statistics": 1, "data_visualization": 1,
    "machine_learning": 2, "scikit_learn": 2, "feature_engineering": 2, "agile_methodology": 2,
    "deep_learning": 3, "tensorflow": 3, "pytorch": 3, "keras": 3, "computer_vision": 3,
    "nlp": 3, "spacy": 3, "opencv": 3, "reinforcement_learning": 3,
    "transformers": 4, "llm": 4, "prompt_engineering": 4, "rag": 4, "langchain": 4,
    "fine_tuning": 4, "vector_database": 4, "embeddings": 4, "generative_ai": 4,
    "fastapi": 4, "docker": 4, "mlops": 4, "system_design": 4, "model_deployment": 4,
    "aws": 4, "azure": 4, "gcp": 4,
}

DIAMOND_CAPSTONE = [
    {"title": "Ship a production-style project", "detail": "One end-to-end project with real data, tests, and a README — this is what recruiters actually open."},
    {"title": "Build a GitHub portfolio", "detail": "Pin 3-4 of your strongest projects with clear commit history, not just a final upload."},
    {"title": "Deploy something", "detail": "Put at least one project behind a live URL (even a free-tier deployment counts)."},
    {"title": "Prepare for system design / interviews", "detail": "Practice explaining trade-offs in your own projects out loud — this is what technical interviews actually probe."},
    {"title": "Resume optimization pass", "detail": "Re-run Resume Improvement (Module 17) once your new projects/skills exist to fold them in."},
]


def _skill_level(skill_key: str, skills_db: dict) -> int:
    if skill_key in LEVEL_OVERRIDES:
        return LEVEL_OVERRIDES[skill_key]
    category = skills_db["skills"].get(skill_key, {}).get("category", "")
    return CATEGORY_DEFAULT_LEVEL.get(category, 2)


def build_roadmap(user_skills: List[str], career_key: str, skills_db: dict) -> Dict:
    gap = recommender.skill_gap(user_skills, career_key, skills_db)
    required_keys = {m["skill"] for m in gap["matched_skills"]} | {m["skill"] for m in gap["missing_skills"]}

    buckets: Dict[int, Dict[str, List]] = {i: {"verified": [], "to_learn": []} for i in range(6)}

    matched_keys = {m["skill"]: m for m in gap["matched_skills"]}
    missing_keys = {m["skill"]: m for m in gap["missing_skills"]}

    for skill_key in required_keys:
        lvl = _skill_level(skill_key, skills_db)
        label = skills_db["skills"][skill_key]["label"]
        if skill_key in matched_keys:
            buckets[lvl]["verified"].append({"skill": skill_key, "label": label, "status": "VERIFIED"})
        else:
            item = missing_keys[skill_key]
            courses = skills_db["courses"].get(skill_key, [])
            project = skills_db["project_ideas"].get(skill_key, f"Build a small project applying {label}.")
            buckets[lvl]["to_learn"].append({
                "skill": skill_key,
                "label": label,
                "status": "TO_LEARN",
                "priority": {3: "Core", 2: "Supporting", 1: "Differentiator"}.get(item["weight"], "Differentiator"),
                "course": courses[0] if courses else None,
                "project": project,
            })

    levels_out = []
    for lvl_meta in LEVELS:
        lvl = lvl_meta["level"]
        if lvl == 5:
            levels_out.append({**lvl_meta, "verified": [], "to_learn": [], "capstone": DIAMOND_CAPSTONE})
            continue
        b = buckets[lvl]
        b["to_learn"].sort(key=lambda s: {"Core": 0, "Supporting": 1, "Differentiator": 2}[s["priority"]])
        levels_out.append({**lvl_meta, "verified": b["verified"], "to_learn": b["to_learn"], "capstone": []})

    return {
        "career": career_key,
        "career_label": gap["career_label"],
        "current_score": gap["current_score"],
        "levels": levels_out,
        "total_verified": len(gap["matched_skills"]),
        "total_to_learn": len(gap["missing_skills"]),
    }
