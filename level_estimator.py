"""
skills/level_estimator.py

Turns "Python = present" into an *estimated* skill level with visible
evidence, per the brief:

    "Do not falsely claim that the system can know someone's exact
    expertise from a resume ... call this an estimated skill level based
    on resume evidence and later assessment results."

Method (fully transparent, no black box):
  - count how many resume sections mention the skill (skills list only vs.
    also appearing inside Projects / Experience, which is much stronger
    evidence of hands-on use than a bare keyword in a skills list)
  - count *how many times* it appears in Projects/Experience specifically
  - combine into a 0-100 evidence score -> Beginner / Intermediate / Advanced
  - confidence reflects how much text evidence backs the estimate, not how
    good the person is

This score later becomes exactly one input (resume_evidence_score) into
the combined Skill Mastery score in skills/mastery.py, alongside real
assessment results — so a resume-only estimate is explicitly a starting
point, not a final grade.
"""
import re
from typing import Dict, List

SECTION_WEIGHTS = {
    "projects": 3,
    "experience": 3,
    "certifications": 1,
    "skills": 1,
    "summary": 1,
    "header": 0,
}


def _alias_patterns(skill_key: str, skills_db: dict) -> List[re.Pattern]:
    aliases = skills_db["skills"][skill_key]["aliases"]
    patterns = []
    for alias in aliases:
        alias = alias.strip()
        if not alias:
            continue
        patterns.append(re.compile(r"(?<![\w+#.-])" + re.escape(alias) + r"(?![\w+#.-])", re.IGNORECASE))
    return patterns


def estimate_skill_level(skill_key: str, sections: Dict[str, str], skills_db: dict) -> Dict:
    patterns = _alias_patterns(skill_key, skills_db)
    label = skills_db["skills"][skill_key]["label"]

    evidence: List[str] = []
    score = 10  # base score just for appearing anywhere at all

    for section_name, weight in SECTION_WEIGHTS.items():
        text = sections.get(section_name, "")
        if not text:
            continue
        hits = sum(1 for p in patterns for _ in p.finditer(text))
        if hits:
            score += min(hits, 3) * weight * 6
            if section_name == "projects":
                evidence.append(f"Mentioned in {hits} project line(s)")
            elif section_name == "experience":
                evidence.append(f"Mentioned in {hits} experience line(s)")
            elif section_name == "skills":
                evidence.append("Listed in the skills section")
            elif section_name == "certifications":
                evidence.append("Referenced near a certification/course entry")
            elif section_name == "summary":
                evidence.append("Mentioned in the summary/objective")

    score = min(100, score)
    if not evidence:
        evidence.append("Detected as a keyword in the resume text")

    if score >= 65:
        level = "Advanced"
    elif score >= 35:
        level = "Intermediate"
    else:
        level = "Beginner"

    confidence = min(95, 30 + len(evidence) * 15 + (10 if score >= 65 else 0))

    return {
        "skill": skill_key,
        "label": label,
        "level": level,
        "confidence": confidence,
        "evidence": evidence,
        "evidence_score": score,
    }


def estimate_all_levels(skill_keys: List[str], full_text: str, sections: Dict[str, str], skills_db: dict) -> Dict[str, Dict]:
    return {key: estimate_skill_level(key, sections, skills_db) for key in skill_keys}
