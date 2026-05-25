import json
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def ddg_search(query: str, max_results: int = 8) -> str:
    max_results = min(max_results, 20)
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        results = [{"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")} for r in raw]
        return json.dumps({"query": query, "num_results": len(results), "results": results}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query, "results": []})

def ddg_news(query: str, max_results: int = 6) -> str:
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results))
        results = [{"title": r.get("title",""), "url": r.get("url",""), "snippet": r.get("body",""), "published": r.get("date","")} for r in raw]
        return json.dumps({"query": query, "num_results": len(results), "news": results}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query, "news": []})