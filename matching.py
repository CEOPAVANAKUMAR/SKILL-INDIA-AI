"""
jobs/matching.py — Module 5: Job Role Matching.

Wraps recommender.rank_jobs() (unchanged scoring) with a readiness status
and recommended next actions per job, and explicitly labels the data
source as a demo/local dataset — the brief requires this: "If no live job
API is connected, clearly label jobs as 'Demo/sample job data'."

Architected so a real job API/dataset can be swapped in later: replace
skills_db["jobs"] with postings fetched from a live source and everything
downstream (matching, readiness labels) keeps working unchanged.
"""
from typing import List

import recommender

READINESS_BANDS = [
    (80, "Ready to apply"),
    (55, "Close — apply while closing small gaps"),
    (30, "Build 2-3 more required skills first"),
    (0, "Early stage for this role"),
]


def _readiness(match_pct: int) -> str:
    for threshold, label in READINESS_BANDS:
        if match_pct >= threshold:
            return label
    return READINESS_BANDS[-1][1]


def match_jobs(user_skills: List[str], skills_db: dict, top_n: int = 10) -> List[dict]:
    ranked = recommender.rank_jobs(user_skills, skills_db, top_n=top_n)
    for row in ranked:
        row["readiness_status"] = _readiness(row["match"])
        row["recommended_action"] = (
            f"Focus on: {', '.join(row['missing_skills'][:3])}" if row["missing_skills"]
            else "All required skills matched — this role is ready to apply to."
        )
        row["data_source"] = "Demo/sample job data (local dataset — not a live posting)"
    return ranked
