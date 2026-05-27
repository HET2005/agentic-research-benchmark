# frameworks/crewai/base.py
import os
import sys
import time
from pathlib import Path

# Crucial LiteLLM environment overrides to prevent caching bugs with Groq/MiniMax
os.environ["LITELLM_CACHE"] = "false"
os.environ["LITELLM_DROP_PARAMS"] = "true"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-dummy-not-used")
os.environ["CREWAI_TRACING_ENABLED"] = "false"

sys.path.insert(0, str(Path(__file__).parents[2]))

from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# MUST explicitly force litellm to drop unsupported params (fixes Groq cache_breakpoint error)
try:
    import litellm
    litellm.drop_params = True
    litellm.cache = None
    litellm.disable_cache = True
except Exception:
    pass

# BUG 3 & 8 FIX: Standardize LLM order to prevent LiteLLM MiniMax timeouts short-circuiting pipelines
def get_shared_llm(seed=None):
    from dotenv import load_dotenv
    load_dotenv()
    
    # Pass seed down to ensure reproducible multi-seed runs (Bug 7 fix)
    kwargs = {}
    if seed is not None:
        kwargs["seed"] = seed

    if os.environ.get("OPENAI_API_KEY") and not os.environ["OPENAI_API_KEY"].startswith("sk-dummy"):
        return LLM(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"], **kwargs)
    if os.environ.get("ANTHROPIC_API_KEY") and not os.environ["ANTHROPIC_API_KEY"].startswith("sk-dummy"):
        return LLM(model="claude-3-haiku-20240307", api_key=os.environ["ANTHROPIC_API_KEY"]) 
    if os.environ.get("GROQ_API_KEY") and not os.environ["GROQ_API_KEY"].startswith("sk-dummy"):
        return LLM(model="groq/llama-3.1-8b-instant", api_key=os.environ["GROQ_API_KEY"], **kwargs)
    if os.environ.get("MINIMAX_API_KEY") and not os.environ["MINIMAX_API_KEY"].startswith("sk-dummy"):
        return LLM(model="openai/MiniMax-Text-01", api_key=os.environ["MINIMAX_API_KEY"], base_url="https://api.minimax.io/v1", **kwargs)
    return None

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(6, description="Max results")

class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the web using DuckDuckGo."
    args_schema: type = WebSearchInput
    def _run(self, query: str, max_results: int = 6) -> str:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            from ddgs import DDGS
        import json
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            return json.dumps({"query": query, "results": [{"title": r.get("title",""), "snippet": r.get("body","")} for r in raw]})
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

class Timer:
    def __init__(self):
        self._start = None
        self.elapsed = 0.0
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start

def _mock_run(question: str, pipeline: str) -> str:
    return f"[CREWAI MOCK - no API key] Pipeline={pipeline} Question={question[:80]}"

def make_agent(role: str, goal: str, backstory: str, tools=None, llm=None) -> Agent:
    return Agent(role=role, goal=goal, backstory=backstory, tools=tools or [], verbose=False, allow_delegation=False, llm=llm or get_shared_llm())

def make_task(description: str, agent: Agent, expected_output: str = "A comprehensive written response.") -> Task:
    return Task(description=description, agent=agent, expected_output=expected_output)

def run_crew(crew: Crew, inputs: dict) -> str:
    try:
        result = crew.kickoff(inputs=inputs)
        return str(result.raw) if hasattr(result, "raw") else str(result)
    except Exception as e:
        err = str(e)
        if any(x in err.lower() for x in ["api", "key", "connect", "openai", "quota", "auth", "cache"]):
            return f"[CREWAI MOCK - API error] {err}"
        return f"[CREW ERROR] {err}"