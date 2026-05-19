"""
AutoGen base utilities — shared LLM caller and tool wrappers.
AutoGen uses a conversational multi-agent pattern.
We simulate this with a lightweight orchestrator+worker pattern
that doesn't require a running Docker/code-exec environment.
"""

import os
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))


def llm_call(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return f"[MOCK] hash={hash(prompt) % 99999}"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system or "You are a helpful research assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"[LLM ERROR] {e}"


def web_search(query: str, max_results: int = 6) -> str:
    from tools.ddg_tool import ddg_search
    return ddg_search(query, max_results=max_results)


def finance_search(query: str) -> str:
    from tools.yf_tool import yf_search
    return yf_search(query)


class Timer:
    def __init__(self):
        self._start = None
        self.elapsed = 0.0
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start


def agent_message(role: str, content: str) -> dict:
    """Simulate an AutoGen-style agent message."""
    return {"role": role, "content": content}


def conversation_turn(orchestrator_prompt: str, worker_system: str,
                      history: list = None, max_tokens: int = 1500) -> str:
    """
    Simulate one AutoGen conversation turn.
    orchestrator sends a message, worker responds.
    History is a list of prior agent_message dicts.
    """
    context = ""
    if history:
        for msg in history[-4:]:  # last 4 turns for context
            context += f"\n[{msg['role']}]: {msg['content'][:300]}\n"
    full_prompt = f"{context}\n[Orchestrator]: {orchestrator_prompt}"
    return llm_call(full_prompt, system=worker_system, max_tokens=max_tokens)


def result_dict(pipeline: str, question: str, answer: str,
                latency: float, run_id: str, seed: int, **extra) -> dict:
    return {
        "pipeline": pipeline, "framework": "autogen",
        "question": question, "answer": answer,
        "latency": latency, "token_count": len(answer.split()),
        "run_id": run_id, "seed": seed, **extra,
    }