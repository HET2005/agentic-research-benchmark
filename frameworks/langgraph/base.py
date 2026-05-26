"""
frameworks/langgraph/base.py
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from frameworks.shared_llm import llm_call  # noqa: F401 — re-exported


def search_web(query: str, max_results: int = 6) -> str:
    from tools.ddg_tool import ddg_search
    return ddg_search(query, max_results=max_results)


def search_finance(query: str) -> str:
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