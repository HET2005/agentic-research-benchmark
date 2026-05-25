"""
LLM-as-judge scoring for benchmark outputs.
Scores each answer on: accuracy, completeness, groundedness, coherence (0-10 each).
"""

import os
import json


def llm_call(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    import json
    from dotenv import load_dotenv
    load_dotenv()

    groq_key = os.environ.get("GROQ_API_KEY", "")
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")

    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=max_tokens,
                messages=messages,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return json.dumps({"error": str(e), "accuracy": 0,
                               "completeness": 0, "groundedness": 0, "coherence": 0})
    else:
        h = abs(hash(prompt)) % 10
        return json.dumps({
            "accuracy": 5 + h % 4, "completeness": 4 + h % 5,
            "groundedness": 5 + h % 3, "coherence": 6 + h % 4,
            "reasoning": "Mock score — no API key set."
        })

def score_answer(question: str, answer: str, rubric: dict) -> dict:
    required_topics = rubric.get("required_topics", [])
    min_words = rubric.get("min_word_count", 200)
    must_cite = rubric.get("must_cite", False)
    word_count = len(answer.split())

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
        '{\"accuracy\": 7, \"completeness\": 6, \"groundedness\": 5, \"coherence\": 8, \"reasoning\": \"explanation here\"}'
    )

    raw = llm_call(prompt, system=system, max_tokens=200)

    # Try multiple JSON extraction strategies
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

    # Strategy 3: extract numbers manually
    if not scores:
        try:
            import re
            nums = re.findall(r'"(accuracy|completeness|groundedness|coherence)"\s*:\s*(\d+)', raw)
            if nums:
                scores = {k: int(v) for k, v in nums}
                scores["reasoning"] = "Extracted from partial response"
        except Exception:
            pass

    # Fallback: rule-based scoring
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