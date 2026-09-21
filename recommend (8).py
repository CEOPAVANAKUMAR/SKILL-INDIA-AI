"""
courses/recommend.py — Module 7: Personalized Course Recommendation.

Important constraint from the brief: "Do not invent course links." The
existing skills_database.json curates exactly one real, named course per
skill (38 of 72 skills). Rather than fabricating two more specifically-
named courses per skill to fill a fake "beginner/intermediate/advanced"
catalog, this module:

  - shows the ONE curated, real course as the named "core resource"
  - additionally describes a beginner stage and an advanced/applied stage
    as *learning-stage guidance*, not specific named courses, and grounds
    the advanced stage in the project already curated for that skill in
    project_ideas (also real, existing data) rather than inventing one

This keeps every claim traceable to data actually in the project.
"""
from typing import Dict, List


def recommend_for_skill(skill_key: str, skills_db: dict, career_label: str = "") -> Dict:
    meta = skills_db["skills"].get(skill_key, {})
    label = meta.get("label", skill_key)
    curated = skills_db["courses"].get(skill_key, [])
    project = skills_db["project_ideas"].get(skill_key, "")

    why_needed = (
        f"Required to close your skill gap for {career_label}." if career_label
        else f"Commonly required alongside your current skills."
    )

    resources = [{
        "stage": "Beginner",
        "type": "guidance",
        "title": f"Learn {label} fundamentals",
        "detail": f"Start with official documentation and structured beginner tutorials for {label} before moving to applied work.",
        "provider": None,
        "duration": "1-2 weeks",
    }]

    if curated:
        resources.append({
            "stage": "Core resource",
            "type": "course",
            "title": curated[0]["name"],
            "detail": f"Curated course for {label}.",
            "provider": curated[0]["platform"],
            "duration": "3-6 weeks (self-paced)",
        })

    if project:
        resources.append({
            "stage": "Advanced / applied",
            "type": "project",
            "title": f"Apply it: {project}",
            "detail": "Hands-on project evidence is weighted heavily in your Skill Mastery score — build this once you're comfortable with the fundamentals.",
            "provider": None,
            "duration": "1-3 weeks",
        })

    return {
        "skill": skill_key,
        "label": label,
        "why_needed": why_needed,
        "resources": resources,
    }


def recommend_courses_for_gap(missing_skills: List[dict], skills_db: dict, career_label: str = "") -> List[Dict]:
    """missing_skills: list of {skill, label, weight, priority} from gap_with_priority()."""
    return [recommend_for_skill(m["skill"], skills_db, career_label) for m in missing_skills]
