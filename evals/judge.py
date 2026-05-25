"""
LLM-as-judge scoring for benchmark outputs.
Scores each answer on: accuracy, completeness, groundedness, coherence (0-10 each).
"""

import os
import json


def llm_call(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    import json, os
    from dotenv import load_dotenv
    load_dotenv()

    groq_key = os.environ.get("GROQ_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

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
            return json.dumps({"error": str(e), "accuracy": 0, "completeness": 0,
                               "groundedness": 0, "coherence": 0})
    else:
        h = abs(hash(prompt)) % 10
        return json.dumps({
            "accuracy": 5 + h % 4, "completeness": 4 + h % 5,
            "groundedness": 5 + h % 3, "coherence": 6 + h % 4,
            "reasoning": "Mock score — no API key set."
        })

def score_answer(question: str, answer: str, rubric: dict) -> dict:
    """
    Score a single answer against a rubric.
    Returns dict with scores 0-10 per dimension + overall.
    """
    required_topics = rubric.get("required_topics", [])
    min_words = rubric.get("min_word_count", 200)
    must_cite = rubric.get("must_cite", False)

    system = (
        "You are an expert research evaluator. "
        "Score the answer strictly on a 0-10 scale for each dimension. "
        "Return ONLY valid JSON with keys: accuracy, completeness, groundedness, coherence, reasoning. "
        "No markdown, no extra text."
    )
    prompt = f"""Research question: {question}

Answer to evaluate:
{answer[:3000]}

Rubric:
- Required topics to cover: {required_topics}
- Minimum word count: {min_words} (actual: {len(answer.split())})
- Must include citations: {must_cite}

Score 0-10 for each:
- accuracy: Are claims factually correct?
- completeness: Are all required topics covered?
- groundedness: Are claims cited/sourced?
- coherence: Is the answer well-structured and clear?
- reasoning: Brief explanation of scores (1-2 sentences)

Return JSON only."""

    raw = llm_call(prompt, system=system)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        scores = json.loads(raw[start:end])
    except Exception:
        scores = {"accuracy": 0, "completeness": 0,
                  "groundedness": 0, "coherence": 0,
                  "reasoning": f"Parse error: {raw[:100]}"}

    # Compute weighted overall
    weights = rubric.get("scoring_weights",
                         {"accuracy": 0.35, "completeness": 0.3,
                          "groundedness": 0.2, "coherence": 0.15})
    overall = sum(
        scores.get(k, 0) * w for k, w in weights.items()
        if k in scores
    )
    scores["overall"] = round(overall, 2)
    scores["word_count"] = len(answer.split())
    return scores


def batch_score(results: list, questions_map: dict) -> list:
    """
    Score a list of run result dicts.
    questions_map: {qid: question_dict} from question_set.py
    Returns list of result dicts with scores added.
    """
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