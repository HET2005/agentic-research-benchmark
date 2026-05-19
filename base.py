"""
frameworks/crewai/base.py
Shared utilities for all CrewAI pipeline implementations.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[2]))

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ── Tool wrappers ─────────────────────────────────────────────────────────────

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(6, description="Max results")


class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the web using DuckDuckGo. Returns top results with titles, URLs, and snippets."
    args_schema: type = WebSearchInput

    def _run(self, query: str, max_results: int = 6) -> str:
        from tools.ddg_tool import ddg_search
        return ddg_search(query, max_results=max_results)


class FinanceSearchInput(BaseModel):
    query: str = Field(..., description="Ticker symbol or company name")
    period: str = Field("1mo", description="Time period")


class FinanceSearchTool(BaseTool):
    name: str = "Financial Data"
    description: str = "Fetch financial market data for stocks/assets using yfinance."
    args_schema: type = FinanceSearchInput

    def _run(self, query: str, period: str = "1mo") -> str:
        from tools.yf_tool import yf_search
        return yf_search(query, period)


# ── LLM configuration ─────────────────────────────────────────────────────────

def get_llm():
    """Return a CrewAI-compatible LLM config."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            from crewai import LLM
            return LLM(model="claude-sonnet-4-20250514", api_key=api_key)
        except Exception:
            pass
    # If no key, CrewAI will use its default (may fail without key)
    return None


# ── Shared tool instances ──────────────────────────────────────────────────────

WEB_TOOL = WebSearchTool()
FINANCE_TOOL = FinanceSearchTool()


# ── Timer ──────────────────────────────────────────────────────────────────────

class Timer:
    def __init__(self):
        self._start = None
        self.elapsed = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start


# ── Crew runner helper ────────────────────────────────────────────────────────

def run_crew(crew: Crew, inputs: dict) -> str:
    """Run a crew and return the final output as a string."""
    try:
        result = crew.kickoff(inputs=inputs)
        # CrewAI result can be CrewOutput object or string
        if hasattr(result, "raw"):
            return str(result.raw)
        return str(result)
    except Exception as e:
        return f"[CREW ERROR] {e}"


def make_agent(role: str, goal: str, backstory: str, tools=None, llm=None) -> Agent:
    """Factory for a CrewAI Agent."""
    kwargs = dict(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools or [],
        verbose=False,
        allow_delegation=False,
    )
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)


def make_task(description: str, agent: Agent, expected_output: str = "A comprehensive written response.") -> Task:
    """Factory for a CrewAI Task."""
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
    )
