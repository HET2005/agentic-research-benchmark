"""
frameworks/autogen/base.py
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from frameworks.shared_llm import llm_call  # noqa: F401 — re-exported


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
    return {"role": role, "content": content}


def conversation_turn(orchestrator_prompt: str, worker_system: str,
                      history: list = None, max_tokens: int = 1500) -> str:
    context = ""
    if history:
        for msg in history[-4:]:
            context += f"\n[{msg['role']}]: {msg['content'][:300]}\n"
    full_prompt = f"{context}\n[Orchestrator]: {orchestrator_prompt}"
    return llm_call(full_prompt, system=worker_system, max_tokens=max_tokens)


def result_dict(pipeline: str, question: str, answer: str,
                latency: float, run_id: str, seed: int, **extra) -> dict:
    return {
        "pipeline": pipeline, "framework": "autogen",
        "question": question, "answer": answer,
        "latency": latency, "word_count": len(answer.split()),
        "run_id": run_id, "seed": seed, **extra,
    }