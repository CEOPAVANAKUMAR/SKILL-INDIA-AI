"""
nlp/text_processing.py — the front half of the NLP pipeline described in
the project brief:

    Resume -> text extraction -> text cleaning -> section detection ->
    sentence/token processing -> (skill/entity extraction happens in
    resume/parser.py, reusing the alias matcher already built for this
    project) -> section-aware structured extraction (education, projects,
    experience, certifications, GitHub links).

Deliberately dependency-light: a small hand-built stopword list and regex
tokenizer instead of nltk/spaCy corpora, so nothing needs a network download
to run. See nlp/similarity.py for where scikit-learn's TF-IDF is used for
the semantic-similarity layer — that's the one place true "NLP maths"
(vectorization + cosine similarity) is used, on top of this deterministic
section/entity layer.
"""
import re
from typing import Dict, List

# A small general-purpose English stopword list (no NLTK corpus download
# required). Good enough for keyword/TF-IDF weighting on resume text.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "of", "in", "on",
    "at", "to", "for", "with", "as", "by", "is", "are", "was", "were", "be",
    "been", "being", "this", "that", "these", "those", "it", "its", "i", "we",
    "you", "he", "she", "they", "my", "our", "your", "their", "from", "up",
    "down", "out", "about", "into", "over", "after", "before", "between",
    "using", "used", "use", "also", "have", "has", "had", "will", "would",
    "can", "could", "should", "may", "might", "not", "no", "do", "did", "does",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z+#.\-]{1,}")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters picked up from PDF/DOCX extraction."""
    text = text.replace("\r", "\n")
    text = re.sub(r"[\t\x0b\x0c]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """Lowercase word tokenizer with stopword removal — used for TF-IDF and keyword overlap."""
    words = [w.lower() for w in WORD_RE.findall(text)]
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def sentences(text: str) -> List[str]:
    """Very small sentence splitter (period/newline/bullet boundaries) — no model needed."""
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [c.strip(" -•\u2022\t") for c in chunks if c.strip(" -•\u2022\t")]


# ---------------------------------------------------------------- sections

SECTION_HEADERS = {
    "education": r"education|academic background|qualification",
    "experience": r"experience|work experience|employment|internship",
    "projects": r"projects?|personal projects?|academic projects?",
    "skills": r"skills?|technical skills?|technologies|tech stack",
    "certifications": r"certifications?|licenses?|courses?( completed)?",
    "summary": r"summary|objective|profile",
}

def split_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into named sections by scanning for short lines that
    look like section headers (e.g. "PROJECTS", "Work Experience:"). Text
    before the first recognized header is returned under "header" (contact
    block / summary). This is the "section detection" stage of the pipeline.
    """
    lines = text.split("\n")
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in lines:
        stripped = line.strip()
        # Section headers are commonly written with a trailing colon or dash
        # ("Education:", "PROJECTS -"), which isn't part of the header word
        # itself, so it must be stripped before matching against SECTION_HEADERS.
        header_candidate = stripped.rstrip(":-—– ").strip()
        matched_section = None
        if 0 < len(header_candidate) <= 40:
            for name, pattern in SECTION_HEADERS.items():
                if re.fullmatch(pattern, header_candidate, re.IGNORECASE):
                    matched_section = name
                    break
        if matched_section:
            current = matched_section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {name: "\n".join(lines_).strip() for name, lines_ in sections.items()}


# ---------------------------------------------------------------- structured

DEGREE_RE = re.compile(
    r"\b(B\.?\s?Tech|B\.?\s?E\.?|Bachelor of \w+|M\.?\s?Tech|M\.?\s?E\.?|"
    r"B\.?\s?Sc|M\.?\s?Sc|MBA|Ph\.?\s?D|Diploma)\b",
    re.IGNORECASE,
)
BRANCH_RE = re.compile(
    r"\b(Computer Science(?: (?:and|&) Engineering)?|CSE|Information Technology|IT|"
    r"Electronics(?: (?:and|&) Communication)?|ECE|Electrical(?: (?:and|&) Electronics)?|EEE|"
    r"Mechanical|Civil|Data Science|Artificial Intelligence(?: (?:and|&) Machine Learning)?|AI\s*&?\s*ML)\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[\w\-]+", re.IGNORECASE)
LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[\w\-]+", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*(\d+[.)]|[-•\u2022*▪])\s*")


def extract_education_struct(text: str, education_lines: List[str]) -> Dict[str, str]:
    """Best-effort degree / branch / graduation-year extraction from education lines."""
    joined = " | ".join(education_lines) if education_lines else text
    degree_m = DEGREE_RE.search(joined)
    branch_m = BRANCH_RE.search(joined)
    years = YEAR_RE.findall(joined)
    grad_year = ""
    if years:
        # findall on a group-capturing pattern returns the captured group; re-search for the full number instead
        all_years = YEAR_RE.finditer(joined)
        nums = [m.group(0) for m in all_years]
        grad_year = max(nums) if nums else ""
    return {
        "degree": degree_m.group(0) if degree_m else "",
        "branch": branch_m.group(0) if branch_m else "",
        "grad_year": grad_year,
    }


def extract_bulleted_items(section_text: str, max_items: int = 12) -> List[str]:
    """
    Pull out bullet/numbered-list items from a section (used for projects,
    experience, certifications). A line is treated as the START of a new
    item if it opens with a bullet character or a number ("1.", "2)");
    any other non-empty line is treated as a wrapped continuation of the
    previous item — common when PDF extraction breaks one logical bullet
    across two lines.
    """
    items: List[str] = []
    for line in section_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        match = BULLET_RE.match(stripped)
        if match:
            cleaned = stripped[match.end():].strip()
            if cleaned:
                items.append(cleaned)
        elif items:
            items[-1] = (items[-1] + " " + stripped).strip()
        elif len(stripped) > 15:
            # No bullet marker ever seen in this section (some resumes just
            # use plain lines) — accept reasonably long standalone lines.
            items.append(stripped)
    return items[:max_items]


def extract_links(text: str) -> Dict[str, str]:
    gh = GITHUB_RE.search(text)
    li = LINKEDIN_RE.search(text)
    return {
        "github": gh.group(0) if gh else "",
        "linkedin": li.group(0) if li else "",
    }
