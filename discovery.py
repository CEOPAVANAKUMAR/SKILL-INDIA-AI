"""
careers/discovery.py — Module 4: Career Discovery Engine (explainable).

Deliberately does NOT re-implement scoring: recommender.rank_careers()
already computes an honest, auditable weighted-overlap match percentage.
This module wraps that result with the "why" every recommendation needs
per the brief's Explainability requirement (#24), plus a readiness label
and a resume-text semantic-similarity signal as a secondary, clearly
labeled signal (not the primary score, so the ranking stays explainable
by skill overlap first).
"""
from typing import List, Optional

import recommender
from nlp.similarity import semantic_similarity

READINESS_BANDS = [
    (75, "Ready to target"),
    (50, "Almost ready"),
    (25, "Needs focused work"),
    (0, "Early stage"),
]


def _readiness(match_pct: int) -> str:
    for threshold, label in READINESS_BANDS:
        if match_pct >= threshold:
            return label
    return READINESS_BANDS[-1][1]


def discover_careers(user_skills: List[str], skills_db: dict, resume_text: Optional[str] = None,
                      top_n: int = 9) -> List[dict]:
    ranked = recommender.rank_careers(user_skills, skills_db, top_n=top_n)
    user_set = set(user_skills)

    for row in ranked:
        career = skills_db["careers"][row["career"]]
        gap = recommender.skill_gap(user_skills, row["career"], skills_db)
        matched_labels = [m["label"] for m in gap["matched_skills"]]

        if matched_labels:
            why = (
                f"Your profile already covers {len(matched_labels)} of "
                f"{row['total_required']} skills this role weighs most: "
                f"{', '.join(matched_labels[:5])}"
                + (", among others." if len(matched_labels) > 5 else ".")
            )
        else:
            why = "No overlapping required skills were found yet — this is an exploratory suggestion based on the career catalog."

        row["why_matched"] = why
        row["readiness"] = _readiness(row["match"])
        row["recommended_next_skills"] = row["top_missing"][:3]

        if resume_text:
            row["resume_semantic_similarity"] = semantic_similarity(resume_text, career["description"])
        else:
            row["resume_semantic_similarity"] = None

    return ranked
