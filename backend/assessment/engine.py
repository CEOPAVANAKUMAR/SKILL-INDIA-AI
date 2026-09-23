"""
assessment/engine.py — Module 11 (grading) + Module 12 (Adaptive Learning Loop).

    LEARN -> PRACTICE -> TEST -> ANALYZE PERFORMANCE -> UPDATE SKILL LEVEL -> RECOMMEND NEXT STEP

build_assessment() strips answers before the question set goes to the
client (so the "test" is actually a test). grade_submission() scores it,
computes topic-wise performance, and returns one of three adaptive
recommendations per the brief's worked example (SQL 42% -> revise;
SQL 91% -> unlock advanced):

    score <  50  -> "revise"    (recommend going back to Learn)
    score <  75  -> "practice"  (more practice needed before retesting)
    score >= 75  -> "advance"   (skill verified, unlock next roadmap step)
"""
from typing import Dict, List

from assessment.question_bank import get_questions, has_assessment


def build_assessment(skill_key: str) -> Dict:
    """Return the question set WITHOUT correct answers — this is what the client sees."""
    questions = get_questions(skill_key)
    client_questions = [
        {"id": q["id"], "type": q["type"], "topic": q["topic"], "prompt": q["prompt"], "options": q["options"]}
        for q in questions
    ]
    return {"skill": skill_key, "questions": client_questions, "total": len(client_questions)}


def grade_submission(skill_key: str, answers: Dict[str, int]) -> Dict:
    """
    answers: {question_id: selected_option_index}
    Returns score/accuracy, topic-wise breakdown, strengths/weaknesses, and
    the adaptive recommendation for what to do next.
    """
    questions = get_questions(skill_key)
    if not questions:
        raise ValueError(f"No assessment available for skill '{skill_key}'")

    topic_stats: Dict[str, Dict[str, int]] = {}
    correct_count = 0
    detail = []

    for q in questions:
        selected = answers.get(q["id"])
        is_correct = selected is not None and int(selected) == q["correct_index"]
        if is_correct:
            correct_count += 1
        topic = q["topic"]
        stats = topic_stats.setdefault(topic, {"correct": 0, "total": 0})
        stats["total"] += 1
        if is_correct:
            stats["correct"] += 1
        detail.append({
            "id": q["id"], "topic": topic, "correct": is_correct,
            "correct_index": q["correct_index"], "explanation": q["explanation"],
        })

    total = len(questions)
    accuracy = round((correct_count / total) * 100, 1) if total else 0.0
    score = round(accuracy)

    topic_breakdown = {
        t: {"correct": s["correct"], "total": s["total"], "pct": round((s["correct"] / s["total"]) * 100)}
        for t, s in topic_stats.items()
    }
    strengths = [t for t, s in topic_breakdown.items() if s["pct"] >= 75]
    weaknesses = [t for t, s in topic_breakdown.items() if s["pct"] < 50]

    if score < 50:
        action = "revise"
        recommendation = "This needs reinforcement — revisit the Learn module for this skill before testing again."
    elif score < 75:
        action = "practice"
        recommendation = "Solid start — do another practice pass on the weaker topics below, then retest."
    else:
        action = "advance"
        recommendation = "Skill verified — this is now marked VERIFIED in your roadmap and mastery score."

    return {
        "skill": skill_key,
        "score": score,
        "accuracy": accuracy,
        "correct_count": correct_count,
        "total": total,
        "topic_breakdown": topic_breakdown,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "action": action,
        "recommendation": recommendation,
        "detail": detail,
    }
