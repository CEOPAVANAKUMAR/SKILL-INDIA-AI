"""
resume_parser.py
Resume Intelligence Engine — Module 1

Extracts raw text from an uploaded resume (PDF / DOCX / TXT) and pulls out
structured signals from it: contact info, education mentions, and — most
importantly — a normalized skill list matched against the skills database.

This uses lightweight regex/keyword matching rather than a heavyweight NER
model so the project runs instantly with no model downloads. Swapping in
spaCy's PhraseMatcher or an LLM-based extractor later is a drop-in upgrade —
see the README for where to plug that in.
"""
import io
import re
from typing import Dict, List, Set

import pdfplumber
import docx


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from a resume file, dispatching on extension."""
    name = (filename or "").lower()

    if name.endswith(".pdf"):
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts)

    if name.endswith(".docx"):
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs)

    # Fallback: treat as plain text
    return file_bytes.decode("utf-8", errors="ignore")


def extract_contact_info(text: str) -> Dict[str, str]:
    """Best-effort extraction of name/email/phone from resume text."""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone_match = re.search(r"(\+?\d[\d\-\s()]{8,}\d)", text)

    # Heuristic: the first non-empty line that isn't an email/phone is often the name
    name = ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "@" in line or re.search(r"\d{5,}", line):
            continue
        if len(line.split()) <= 5:
            name = line
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
    }


EDUCATION_KEYWORDS = [
    "b.tech", "btech", "b.e.", "bachelor", "m.tech", "mtech", "master",
    "b.sc", "bsc", "m.sc", "msc", "mba", "phd", "ph.d", "diploma",
]


def extract_education(text: str) -> List[str]:
    """Return the lines that look like they mention an education credential."""
    hits = []
    for line in text.splitlines():
        low = line.lower()
        if any(kw in low for kw in EDUCATION_KEYWORDS):
            cleaned = line.strip()
            if cleaned and cleaned not in hits:
                hits.append(cleaned)
    return hits[:6]


def _build_alias_index(skills_db: dict) -> List[tuple]:
    """
    Build a flat list of (compiled_regex, canonical_skill_key), longest alias
    first, so multi-word aliases like "machine learning" are matched before
    shorter overlapping ones.
    """
    entries = []
    for key, meta in skills_db["skills"].items():
        for alias in meta["aliases"]:
            alias = alias.strip()
            if not alias:
                continue
            pattern = re.compile(
                r"(?<![\w+#.-])" + re.escape(alias) + r"(?![\w+#.-])",
                re.IGNORECASE,
            )
            entries.append((len(alias), pattern, key))
    entries.sort(key=lambda e: e[0], reverse=True)
    return [(p, k) for _, p, k in entries]


_ALIAS_INDEX_CACHE = {}


def extract_skills(text: str, skills_db: dict) -> List[str]:
    """
    Scan resume text for every known skill alias and return the set of
    canonical skill keys found, sorted by category then label for a stable,
    readable order.
    """
    cache_key = id(skills_db)
    if cache_key not in _ALIAS_INDEX_CACHE:
        _ALIAS_INDEX_CACHE[cache_key] = _build_alias_index(skills_db)
    alias_index = _ALIAS_INDEX_CACHE[cache_key]

    found: Set[str] = set()
    for pattern, key in alias_index:
        if pattern.search(text):
            found.add(key)

    def sort_key(k):
        meta = skills_db["skills"][k]
        return (meta["category"], meta["label"])

    return sorted(found, key=sort_key)


def parse_resume(file_bytes: bytes, filename: str, skills_db: dict) -> dict:
    """Run the full Resume Intelligence pipeline and return a profile dict."""
    text = extract_text(file_bytes, filename)
    contact = extract_contact_info(text)
    education = extract_education(text)
    skills = extract_skills(text, skills_db)

    return {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "education": education,
        "extracted_skills": skills,
        "extracted_skill_labels": [skills_db["skills"][k]["label"] for k in skills],
        "raw_text_preview": text[:1200],
        "char_count": len(text),
        # Internal only — used by app.py to run resume_tips() against the FULL
        # document instead of the 1200-char preview, then stripped before the
        # response is sent to the client. See app.py for the bug this fixes.
        "_raw_text_full": text,
    }
