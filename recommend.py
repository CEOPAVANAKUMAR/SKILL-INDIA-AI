"""
projects/recommend.py — Module 14: Project Recommendation Engine.

skills_database.json curates one solid project idea per skill (38 skills).
This module turns that single idea into a Beginner -> Portfolio-level
progression by wrapping it with a fixed, skill-agnostic difficulty ladder
description, rather than inventing three unrelated fake project names per
skill. The one concrete, curated idea is always shown as the "Intermediate"
rung since that's realistically where most of these ideas sit in scope.
"""
from typing import Dict, List

_LADDER_TEXT = {
    "Beginner": "Recreate the core mechanic in isolation with a tiny dataset or toy input — the goal is a working end-to-end pipeline, not polish.",
    "Portfolio-level": "Package the intermediate project with a clean README, a couple of real evaluation numbers, and (if applicable) a small deployed demo — this is the version to link from a resume.",
}


def recommend_projects_for_skill(skill_key: str, skills_db: dict) -> Dict:
    meta = skills_db["skills"].get(skill_key, {})
    label = meta.get("label", skill_key)
    idea = skills_db["project_ideas"].get(skill_key, "")

    ladder = [{
        "difficulty": "Beginner",
        "objective": _LADDER_TEXT["Beginner"],
        "skills_learned": [label],
    }]
    if idea:
        ladder.append({
            "difficulty": "Intermediate",
            "objective": idea,
            "skills_learned": [label],
        })
        ladder.append({
            "difficulty": "Portfolio-level",
            "objective": _LADDER_TEXT["Portfolio-level"],
            "skills_learned": [label],
        })
    return {"skill": skill_key, "label": label, "ladder": ladder, "has_curated_idea": bool(idea)}


def recommend_projects_for_gap(skill_keys: List[str], skills_db: dict) -> List[Dict]:
    return [recommend_projects_for_skill(k, skills_db) for k in skill_keys]
