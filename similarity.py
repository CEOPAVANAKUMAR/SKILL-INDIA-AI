"""
nlp/similarity.py — the semantic-matching layer of the NLP pipeline.

Uses scikit-learn's TfidfVectorizer + cosine_similarity when available
(this is a real, lightweight NLP technique — no model download required,
unlike sentence-transformers). If scikit-learn isn't installed for some
reason, we fall back to a pure-Python term-frequency cosine similarity so
the feature still degrades gracefully rather than throwing errors.

This is used to explain *why* a career or job was recommended in language
beyond "these N keywords matched" — e.g. scoring how closely a resume's
free text overlaps with a career's description, which catches related
phrasing the deterministic alias matcher wouldn't (a resume that says
"built neural networks for image tagging" semantically relates to
Computer Vision even before "computer vision" is normalized as a skill).
"""
import math
from collections import Counter
from typing import List, Tuple

from nlp.text_processing import tokenize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _sk_cosine
    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when sklearn is missing
    SKLEARN_AVAILABLE = False


def _fallback_cosine(text_a: str, text_b: str) -> float:
    """Pure-Python term-frequency cosine similarity — no external dependency."""
    tokens_a, tokens_b = tokenize(text_a), tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    vec_a, vec_b = Counter(tokens_a), Counter(tokens_b)
    shared = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_similarity(text_a: str, text_b: str) -> float:
    """Return a 0..1 similarity score between two pieces of text."""
    if not text_a or not text_b:
        return 0.0
    if not SKLEARN_AVAILABLE:
        return round(_fallback_cosine(text_a, text_b), 4)
    try:
        vec = TfidfVectorizer(stop_words="english")
        matrix = vec.fit_transform([text_a, text_b])
        score = _sk_cosine(matrix[0:1], matrix[1:2])[0][0]
        return round(float(score), 4)
    except Exception:
        return round(_fallback_cosine(text_a, text_b), 4)


def rank_by_similarity(query_text: str, candidates: List[Tuple[str, str]]) -> List[Tuple[str, float]]:
    """
    Rank a list of (key, text) candidates by semantic similarity to query_text.
    Returns [(key, score), ...] sorted best-first.
    """
    scored = [(key, semantic_similarity(query_text, text)) for key, text in candidates]
    scored.sort(key=lambda kv: kv[1], reverse=True)
    return scored
