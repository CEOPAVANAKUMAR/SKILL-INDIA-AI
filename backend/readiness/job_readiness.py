"""
readiness/job_readiness.py — Module 15: "AM I JOB READY?"

Computes six separate readiness dimensions rather than one opaque number,
per the brief. None of these are presented as a guarantee — every response
carries the literal caveat string required by the brief ("Current
estimated readiness based on available evidence").

Dimension sources (all traceable to real data already in this app):
    technical   -> skill_gap() coverage of the target career's required skills
    project     -> number of resume-extracted projects + curated project ideas completed (learning_progress)
    assessment  -> average assessment score across this career's required skills that have been tested
    portfolio   -> whether a GitHub link was found on the resume
    resume      -> inverse of how many resume_tips fired (fewer issues -> higher score)
    interview   -> a lightweight proxy: how consistently the other 5 dimensions score well
                   (explicitly labeled as the weakest-evidence dimension in the response)
"""
from typing import Dict, List, Optional

import recommender


def _resume_score(tips: List[str]) -> float:
    # 1 tip is normal (there's always a "looks solid" tip); each additional issue costs 15 pts.
    issues = max(0, len(tips) - 1)
    return max(20.0, 100.0 - issues * 15.0)


def _project_score(resume_projects: Optional[List[str]], verified_project_count: int) -> float:
    n = (len(resume_projects) if resume_projects else 0) + verified_project_count
    return min(100.0, n * 20.0)


def _assessment_score(assessment_rows: List[Dict], required_skill_keys: set) -> Optional[float]:
    relevant = [r["score"] for r in assessment_rows if r["skill_key"] in required_skill_keys]
    if not relevant:
        return None
    return round(sum(relevant) / len(relevant), 1)


def compute_job_readiness(user_skills: List[str], career_key: str, skills_db: dict,
                           resume_projects: Optional[List[str]] = None,
                           github: str = "", resume_tips: Optional[List[str]] = None,
                           assessment_rows: Optional[List[Dict]] = None,
                           verified_project_count: int = 0) -> Dict:
    gap = recommender.skill_gap(user_skills, career_key, skills_db)
    required_keys = {m["skill"] for m in gap["matched_skills"]} | {m["skill"] for m in gap["missing_skills"]}

    technical = float(gap["current_score"])
    project = _project_score(resume_projects, verified_project_count)
    portfolio = 85.0 if github else 25.0
    resume_score = _resume_score(resume_tips or ["placeholder"])
    assessment_avg = _assessment_score(assessment_rows or [], required_keys)
    assessment_score = assessment_avg if assessment_avg is not None else 0.0

    # Interview readiness has the weakest real evidence in a resume-only demo,
    # so it's derived as a light proxy from the others rather than invented outright.
    interview = round((technical + assessment_score + project) / 3, 1)

    dims = {
        "technical": round(technical, 1),
        "project": round(project, 1),
        "assessment": round(assessment_score, 1) if assessment_avg is not None else None,
        "portfolio": round(portfolio, 1),
        "resume": round(resume_score, 1),
        "interview": interview,
    }
    scored_dims = [v for v in dims.values() if v is not None]
    overall = round(sum(scored_dims) / len(scored_dims), 1) if scored_dims else 0.0

    if overall >= 75:
        summary = "Strong estimated readiness for this role based on available evidence."
    elif overall >= 50:
        summary = "Moderate estimated readiness — a few dimensions below need attention."
    else:
        summary = "Early-stage estimated readiness — focus on the lowest-scoring dimensions first."

    return {
        "career": career_key,
        "career_label": gap["career_label"],
        "dimensions": dims,
        "overall_readiness": overall,
        "summary": summary,
        "caveat": "Current estimated readiness based on available evidence — not a guarantee of employment or exact expertise.",
        "assessment_dimension_note": "Assessment score is None if no relevant skill has been tested yet; interview readiness is the dimension with the weakest direct evidence in a resume-only demo and is estimated from the others.",
    }
