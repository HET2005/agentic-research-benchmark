"""
tools/ddg_tool.py — DuckDuckGo search with retry/backoff.
"""
import json
import time


def ddg_search(query: str, max_results: int = 8, retries: int = 3) -> str:
    max_results = min(max_results, 20)
    for attempt in range(retries):
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            time.sleep(0.5 * attempt)  # backoff
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            results = [
                {"title": r.get("title", ""), "url": r.get("href", ""),
                 "snippet": r.get("body", "")} for r in raw
            ]
            return json.dumps({
                "query": query, "num_results": len(results), "results": results
            }, indent=2)
        except Exception as e:
            if attempt == retries - 1:
                return json.dumps({"error": str(e), "query": query, "results": []})
            time.sleep(1.5 ** attempt)


def ddg_news(query: str, max_results: int = 6) -> str:
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results))
        results = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("body", ""), "published": r.get("date", "")}
            for r in raw
        ]
        return json.dumps({"query": query, "num_results": len(results), "news": results}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query, "news": []})