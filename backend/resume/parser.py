"""
resume/parser.py — Module 1: Resume Intelligence Engine (NLP-upgraded)

Full pipeline:
    file bytes -> extract_text (legacy, unchanged: pdfplumber / python-docx)
    -> clean_text -> split_sections -> per-section structured extraction
    -> extract_skills (legacy alias matcher, reused as-is — it's already a
       solid deterministic NER-style matcher over the skills database)
    -> skill level estimation (skills/level_estimator.py)
    -> ResumeProfile dict

This module *wraps and extends* resume_parser_legacy.py rather than
replacing it: text extraction and skill-alias matching were already
correct and are reused unchanged, per the brief's "improve rather than
replace what already works."
"""
from typing import Dict, List

import resume_parser_legacy as legacy
from nlp import text_processing as tp
from skills.level_estimator import estimate_all_levels


def parse_resume_full(file_bytes: bytes, filename: str, skills_db: dict) -> dict:
    raw_text = legacy.extract_text(file_bytes, filename)
    cleaned = tp.clean_text(raw_text)

    contact = legacy.extract_contact_info(cleaned)
    sections = tp.split_sections(cleaned)

    education_lines = legacy.extract_education(cleaned)
    edu_struct = tp.extract_education_struct(cleaned, education_lines)
    links = tp.extract_links(cleaned)

    projects = tp.extract_bulleted_items(sections.get("projects", ""), max_items=12)
    experience = tp.extract_bulleted_items(sections.get("experience", ""), max_items=10)
    certifications = tp.extract_bulleted_items(sections.get("certifications", ""), max_items=10)

    skills = legacy.extract_skills(cleaned, skills_db)
    skill_labels = [skills_db["skills"][k]["label"] for k in skills]

    level_by_skill = estimate_all_levels(skills, cleaned, sections, skills_db)

    return {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "degree": edu_struct["degree"],
        "branch": edu_struct["branch"],
        "grad_year": edu_struct["grad_year"],
        "github": links["github"],
        "linkedin": links["linkedin"],
        "education": education_lines,
        "projects": projects,
        "experience": experience,
        "certifications": certifications,
        "extracted_skills": skills,
        "extracted_skill_labels": skill_labels,
        "skill_levels": level_by_skill,  # {skill_key: {level, confidence, evidence:[...]}}
        "raw_text_preview": cleaned[:1200],
        "char_count": len(cleaned),
        "sections_detected": [s for s in sections.keys() if s != "header" and sections[s]],
        "_raw_text_full": cleaned,
    }
