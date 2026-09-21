"""
llm_chat.py
Optional LLM Integration (Module 7 upgrade path).

The rule-based chatbot in recommender.chat_reply() works with zero setup.
This module is the "real LLM" version: it sends the user's question plus
their actual skill-gap numbers to Claude so the reply is fluent and
conversational but still grounded in real data instead of the model
guessing at requirements.

Activate it by setting an environment variable before starting the server:
    export ANTHROPIC_API_KEY=sk-ant-...
The app falls back to the rule-based reply automatically if the key isn't
set, or if the request fails for any reason (offline, invalid key, etc.).
"""
import os
from typing import List, Optional

import requests

from recommender import rank_careers, skill_gap

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _build_context(user_skills: List[str], skills_db: dict) -> str:
    """Summarize the user's real skill-gap numbers across every known career
    so the model has grounded data instead of needing to invent it."""
    lines = []
    for row in rank_careers(user_skills, skills_db, top_n=9):
        gap = skill_gap(user_skills, row["career"], skills_db)
        missing = ", ".join(m["label"] for m in gap["missing_skills"][:6]) or "none"
        lines.append(f"- {row['career_label']}: {row['match']}% match. Missing: {missing}")
    return "\n".join(lines)


def get_llm_reply(message: str, user_skills: List[str], skills_db: dict) -> Optional[str]:
    """Return a Claude-generated reply, or None if the API isn't configured
    or the call fails (caller should fall back to the rule-based reply)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    context = _build_context(user_skills, skills_db)
    skill_labels = ", ".join(skills_db["skills"][s]["label"] for s in user_skills) or "none listed yet"

    system_prompt = (
        "You are SkillMind AI, a career readiness assistant embedded in a student's "
        "skill-tracking dashboard. Answer the user's question using ONLY the skill-gap "
        "data provided below — do not invent skill requirements or match percentages. "
        "Be concise (3-5 sentences), specific, and encouraging.\n\n"
        f"User's current skills: {skill_labels}\n\n"
        f"Career fit data:\n{context}"
    )

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 400,
                "system": system_prompt,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
        return "\n".join(parts).strip() or None
    except Exception:
        return None
