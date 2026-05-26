"""
evals/judge.py
LLM-as-judge scoring with error detection and robust fallback.
"""
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

ERROR_PREFIXES = (
    "[LLM ERROR]", "[MOCK]", "[CREWAI MOCK", "[CREW ERROR]",
    "[NO_API_KEY]", "[CREWAI MOCK - API error]"
)


def llm_call(prompt: str, system: str = "", max_tokens: int = 500) -> str:
    """Use shared LLM for judging."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from frameworks.shared_llm import llm_call as _llm
    return _llm(prompt, system=system, max_tokens=max_tokens)


def is_error_answer(answer: str) -> bool:
    """Check if answer is an error/mock string."""
    if not answer or len(answer.strip()) < 10:
        return True
    for prefix in ERROR_PREFIXES:
        if answer.strip().startswith(prefix):
            return True
    return False


def score_answer(question: str, answer: str, rubric: dict) -> dict:
    """Score a single answer. Returns zero scores for error answers."""

    required_topics = rubric.get("required_topics", [])
    min_words = rubric.get("min_word_count", 200)
    must_cite = rubric.get("must_cite", False)
    word_count = len(answer.split())

    # Return zeros immediately for error/mock answers
    if is_error_answer(answer):
        return {
            "accuracy": 0, "completeness": 0,
            "groundedness": 0, "coherence": 0,
            "overall": 0.0, "word_count": word_count,
            "reasoning": "Error or mock answer — not scored."
        }

    system = (
        "You are a research evaluator. Score the answer on 4 dimensions from 0-10. "
        "Return ONLY a valid JSON object with exactly these keys: "
        "accuracy, completeness, groundedness, coherence, reasoning. "
        "No markdown, no backticks, no extra text. Just the JSON object."
    )

    topics_str = ", ".join(required_topics[:5])
    prompt = (
        f"Question: {question[:200]}\n\n"
        f"Answer (first 1000 chars): {answer[:1000]}\n\n"
        f"Required topics to cover: {topics_str}\n"
        f"Word count: {word_count} (minimum: {min_words})\n\n"
        "Score each 0-10:\n"
        "- accuracy: Are facts correct?\n"
        "- completeness: Are required topics covered?\n"
        "- groundedness: Are claims supported?\n"
        "- coherence: Is it well structured?\n"
        "- reasoning: One sentence explanation\n\n"
        "Return ONLY JSON like: "
        '{\"accuracy\": 7, \"completeness\": 6, \"groundedness\": 5, '
        '\"coherence\": 8, \"reasoning\": \"explanation here\"}'
    )

    raw = llm_call(prompt, system=system, max_tokens=300)
    scores = None

    # Strategy 1: direct parse
    try:
        scores = json.loads(raw.strip())
    except Exception:
        pass

    # Strategy 2: find JSON object in response
    if not scores:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                scores = json.loads(raw[start:end])
        except Exception:
            pass

    # Strategy 3: regex extraction
    if not scores:
        try:
            nums = re.findall(
                r'"(accuracy|completeness|groundedness|coherence)"\s*:\s*(\d+)', raw)
            if nums:
                scores = {k: int(v) for k, v in nums}
                scores["reasoning"] = "Extracted from partial response"
        except Exception:
            pass

    # Strategy 4: rule-based fallback
    if not scores:
        covered = sum(1 for t in required_topics if t.lower() in answer.lower())
        completeness = min(10, int((covered / max(len(required_topics), 1)) * 10))
        word_score = min(10, int((word_count / max(min_words, 1)) * 7))
        scores = {
            "accuracy": word_score,
            "completeness": completeness,
            "groundedness": 5 if must_cite and "[source" in answer.lower() else 3,
            "coherence": 6 if word_count > 100 else 3,
            "reasoning": "Rule-based fallback score"
        }

    # Compute weighted overall
    weights = rubric.get("scoring_weights",
                         {"accuracy": 0.35, "completeness": 0.3,
                          "groundedness": 0.2, "coherence": 0.15})
    overall = sum(
        float(scores.get(k, 0)) * w
        for k, w in weights.items()
        if k in scores
    )
    scores["overall"] = round(overall, 2)
    scores["word_count"] = word_count
    return scores


def batch_score(results: list, questions_map: dict) -> list:
    scored = []
    for r in results:
        qid = r.get("question_id", "")
        q_data = questions_map.get(qid, {})
        rubric = q_data.get("rubric", {})
        question = r.get("question", "")
        answer = r.get("answer", "")
        if rubric and answer:
            scores = score_answer(question, answer, rubric)
        else:
            scores = {"accuracy": 0, "completeness": 0,
                      "groundedness": 0, "coherence": 0, "overall": 0}
        scored.append({**r, **scores})
    return scored