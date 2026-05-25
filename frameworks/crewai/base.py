"""
frameworks/crewai/base.py
"""

import os
import sys
import time
from pathlib import Path

os.environ["LITELLM_CACHE"] = "false"
os.environ["LITELLM_DROP_PARAMS"] = "true"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-dummy-not-used")
os.environ["CREWAI_TRACING_ENABLED"] = "false"

sys.path.insert(0, str(Path(__file__).parents[2]))

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# ── Patch litellm directly after import ───────────────────────────────────────
try:
    import litellm
    litellm.drop_params = True
    litellm.cache = None
    litellm.disable_cache = True
except Exception:
    pass

# ── LLM ───────────────────────────────────────────────────────────────────────

def get_llm():
    from dotenv import load_dotenv
    load_dotenv()

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if gemini_key:
        return LLM(
            model="gemini/gemini-2.0-flash",
            api_key=gemini_key,
        )
    elif groq_key:
        return LLM(
            model="groq/llama-3.1-8b-instant",
            api_key=groq_key,
        )
    elif anthropic_key and not anthropic_key.startswith("sk-dummy"):
        return LLM(
            model="anthropic/claude-haiku-4-5-20251001",
            api_key=anthropic_key,
        )
    elif openai_key and not openai_key.startswith("sk-dummy"):
        return LLM(
            model="gpt-4o-mini",
            api_key=openai_key,
        )
    return None

# ── Tools ─────────────────────────────────────────────────────────────────────

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(6, description="Max results")


class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the web using DuckDuckGo."
    args_schema: type = WebSearchInput

    def _run(self, query: str, max_results: int = 6) -> str:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        import json
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            results = [{"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")} for r in raw]
            return json.dumps({"query": query, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e), "results": []})


class FinanceSearchInput(BaseModel):
    query: str = Field(..., description="Ticker or company name")


class FinanceSearchTool(BaseTool):
    name: str = "Financial Data"
    description: str = "Fetch stock market data using yfinance."
    args_schema: type = FinanceSearchInput

    def _run(self, query: str) -> str:
        from tools.yf_tool import yf_search
        return yf_search(query)


WEB_TOOL = WebSearchTool()
FINANCE_TOOL = FinanceSearchTool()


# ── Timer ─────────────────────────────────────────────────────────────────────

class Timer:
    def __init__(self):
        self._start = None
        self.elapsed = 0.0
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start


# ── Mock fallback ─────────────────────────────────────────────────────────────

def _mock_run(question: str, pipeline: str) -> str:
    return f"[CREWAI MOCK - no API key] Pipeline={pipeline} Question={question[:80]}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_agent(role: str, goal: str, backstory: str, tools=None, llm=None) -> Agent:
    kwargs = dict(role=role, goal=goal, backstory=backstory,
                  tools=tools or [], verbose=False, allow_delegation=False)
    resolved_llm = llm or get_llm()
    if resolved_llm:
        kwargs["llm"] = resolved_llm
    return Agent(**kwargs)


def make_task(description: str, agent: Agent,
              expected_output: str = "A comprehensive written response.") -> Task:
    return Task(description=description, agent=agent, expected_output=expected_output)


def run_crew(crew: Crew, inputs: dict) -> str:
    try:
        result = crew.kickoff(inputs=inputs)
        if hasattr(result, "raw"):
            return str(result.raw)
        return str(result)
    except Exception as e:
        err = str(e)
        if any(x in err.lower() for x in ["api", "key", "connect", "openai", "quota", "auth", "cache"]):
            q = inputs.get("question", "unknown")
            return f"[CREWAI MOCK - no valid API key] question={q[:60]}"
        return f"[CREW ERROR] {err}"