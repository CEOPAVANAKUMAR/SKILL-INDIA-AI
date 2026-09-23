"""
resume/improve.py — Module 17: Resume Improvement (post-training re-analysis).

Wraps the existing recommender.resume_tips() (unchanged, still runs first)
and adds a structured breakdown: strengths, missing sections, weak project
descriptions, missing metrics, and missing skills relative to a target
career — without fabricating achievements the resume doesn't contain.
"""
import re
from typing import Dict, List, Optional

import recommender

EXPECTED_SECTIONS = ["education", "projects", "experience", "skills", "certifications"]
SECTION_DISPLAY = {
    "education": "Education", "projects": "Projects", "experience": "Experience",
    "skills": "Skills", "certifications": "Certifications",
}

METRIC_RE = re.compile(r"\d+(\.\d+)?\s*(%|percent|x|ms|s\b|users|k\b|million|thousand)", re.IGNORECASE)


def analyze_resume(full_text: str, sections: Dict[str, str], projects: List[str],
                    detected_skills: List[str], target_career_key: Optional[str] = None,
                    skills_db: Optional[dict] = None) -> Dict:
    base_tips = recommender.resume_tips(full_text)

    strengths = []
    missing_sections = []
    for sec in EXPECTED_SECTIONS:
        if sections.get(sec, "").strip():
            strengths.append(f"{SECTION_DISPLAY[sec]} section detected")
        else:
            missing_sections.append(SECTION_DISPLAY[sec])

    weak_projects = [p for p in projects if len(p) < 40]
    metric_projects = [p for p in projects if METRIC_RE.search(p)]
    missing_metrics = len(projects) > 0 and not metric_projects

    recommended_improvements = list(base_tips)
    if missing_sections:
        recommended_improvements.append(
            f"Add a clear {', '.join(missing_sections)} section — resume parsers (including this one) rely on section headers to find your content."
        )
    if weak_projects:
        recommended_improvements.append(
            f"{len(weak_projects)} project line(s) look very short — expand them with problem, approach, and result."
        )
    if missing_metrics:
        recommended_improvements.append(
            "None of your project lines include a number — add at least one measurable outcome per project (%, time saved, scale, accuracy)."
        )

    missing_skills_for_target: List[str] = []
    target_label = ""
    if target_career_key and skills_db and target_career_key in skills_db["careers"]:
        gap = recommender.skill_gap(detected_skills, target_career_key, skills_db)
        missing_skills_for_target = [m["label"] for m in gap["missing_skills"][:6]]
        target_label = gap["career_label"]
        if missing_skills_for_target:
            recommended_improvements.append(
                f"For {target_label}, your resume doesn't yet show evidence of: {', '.join(missing_skills_for_target)}. "
                "Add these once you've actually built with them — don't list unverified skills."
            )

    return {
        "strengths": strengths,
        "missing_sections": missing_sections,
        "weak_project_descriptions": weak_projects,
        "missing_metrics": missing_metrics,
        "missing_skills_for_target": missing_skills_for_target,
        "target_career": target_label,
        "recommended_improvements": recommended_improvements,
    }
