"""
skills/gap_priority.py — Module 6 (Skill Gap Engine) + Module 8 ("Extra
Skills I Need" Engine), built on top of the existing recommender.skill_gap()
rather than duplicating its scoring.

Priority tiers reuse the *existing* required_skills weight already present
in skills_database.json (1/2/3) instead of inventing a new data structure:

    weight 3 -> Core        (must learn — heavily weighted in this career)
    weight 2 -> Supporting  (strongly useful)
    weight 1 -> Differentiator (nice-to-have, makes the profile stand out)

Learning order is simply the existing weight-descending sort recommender.py
already produces (heaviest / most foundational gaps first) — this module
just labels that order explicitly as "learning_order" in the response.
"""
from typing import List

import recommender

TIER_BY_WEIGHT = {3: "Core", 2: "Supporting", 1: "Differentiator"}


def _tier(weight: int) -> str:
    return TIER_BY_WEIGHT.get(weight, "Differentiator")


def gap_with_priority(user_skills: List[str], career_key: str, skills_db: dict) -> dict:
    gap = recommender.skill_gap(user_skills, career_key, skills_db)

    for item in gap["missing_skills"]:
        item["priority"] = _tier(item["weight"])
    for item in gap["matched_skills"]:
        item["priority"] = _tier(item["weight"])

    core = [m for m in gap["missing_skills"] if m["priority"] == "Core"]
    supporting = [m for m in gap["missing_skills"] if m["priority"] == "Supporting"]
    differentiator = [m for m in gap["missing_skills"] if m["priority"] == "Differentiator"]

    gap["extra_skills"] = {
        "core": core,
        "supporting": supporting,
        "differentiator": differentiator,
    }
    gap["learning_order"] = [m["skill"] for m in gap["missing_skills"]]  # already weight-desc sorted
    return gap
