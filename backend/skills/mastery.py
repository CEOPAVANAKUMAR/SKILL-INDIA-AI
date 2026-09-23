"""
skills/mastery.py — "SkillMind Estimated Mastery" (Module 13)

    Skill Mastery = Resume Evidence + Learning Progress + Practice
                    Performance + Assessment Performance + Project Evidence

The brief is explicit that this must NOT be presented as an objective,
perfect measurement — so the API response always includes the component
breakdown and the literal label "SkillMind Estimated Mastery", never a
bare "Mastery" number with no explanation attached.

Weights are a simple, documented, editable constant — not learned from
data — because for a college-project demo, an explainable weighted sum
that a reviewer can verify by hand beats an opaque model.
"""
from typing import Dict

WEIGHTS = {
    "resume_evidence": 0.20,
    "learning": 0.15,
    "practice": 0.15,
    "assessment": 0.35,
    "project": 0.15,
}

STATUS_BANDS = [
    (85, "Advanced — job-ready depth"),
    (65, "Intermediate — progressing toward advanced"),
    (40, "Intermediate — building confidence"),
    (0, "Beginner — just getting started"),
]


def status_for_score(score: float) -> str:
    for threshold, label in STATUS_BANDS:
        if score >= threshold:
            return label
    return STATUS_BANDS[-1][1]


def compute_mastery(resume_evidence_score: float, learning_score: float,
                     practice_score: float, assessment_score: float,
                     project_score: float) -> Dict:
    """All inputs are 0-100. Returns the weighted estimate + breakdown."""
    estimated = (
        resume_evidence_score * WEIGHTS["resume_evidence"]
        + learning_score * WEIGHTS["learning"]
        + practice_score * WEIGHTS["practice"]
        + assessment_score * WEIGHTS["assessment"]
        + project_score * WEIGHTS["project"]
    )
    estimated = round(min(100, max(0, estimated)), 1)
    return {
        "components": {
            "resume_evidence": round(resume_evidence_score, 1),
            "learning_progress": round(learning_score, 1),
            "practice_performance": round(practice_score, 1),
            "assessment_performance": round(assessment_score, 1),
            "project_evidence": round(project_score, 1),
        },
        "weights": WEIGHTS,
        "estimated_mastery": estimated,
        "status": status_for_score(estimated),
        "label": "SkillMind Estimated Mastery",
    }


def learning_progress_to_score(status: str) -> float:
    """Convert a learning_progress.status value into a 0-100 sub-score."""
    return {
        "not_started": 0,
        "learning": 40,
        "practiced": 65,
        "tested": 80,
        "verified": 100,
    }.get(status, 0)
