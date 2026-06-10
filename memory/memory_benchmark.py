# memory/memory_benchmark.py
"""
Standalone memory benchmark.
Tests each solution on pattern extraction and recall across
research + finance multi-turn conversations.

Run with:
    python -m memory.memory_benchmark
or:
    python memory/memory_benchmark.py
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parents[1]))

from frameworks.shared_llm import llm_call

# ── Conversation scenarios ────────────────────────────────────────────────────

RESEARCH_CONVERSATION = [
    ("user",      "What are the main drivers of AI adoption in enterprise software?"),
    ("assistant", "The main drivers include cost reduction through automation, improved decision-making via predictive analytics, competitive pressure from AI-native startups, and availability of cloud-based AI APIs that lower the barrier to entry."),
    ("user",      "Which industries are leading in AI adoption?"),
    ("assistant", "Financial services, healthcare, and retail lead adoption. Finance uses AI for fraud detection and algorithmic trading. Healthcare applies it to diagnostics and drug discovery. Retail leverages it for recommendation engines and supply chain optimisation."),
    ("user",      "What are the biggest barriers to AI adoption?"),
    ("assistant", "Key barriers include data quality and availability issues, lack of AI talent, regulatory uncertainty especially in healthcare and finance, high implementation costs, and organisational resistance to change."),
    ("user",      "How does AI adoption differ between large enterprises and SMEs?"),
    ("assistant", "Large enterprises have dedicated AI teams and budgets but move slowly due to legacy systems. SMEs can adopt faster due to agility but are constrained by budget and talent. Cloud AI APIs have partially bridged this gap for SMEs."),
    ("user",      "Summarise what we've discussed about barriers and industry leaders so far."),
]

FINANCE_CONVERSATION = [
    ("user",      "Explain how the Federal Reserve's rate hiking cycle of 2022-2023 affected equity markets."),
    ("assistant", "The Fed raised rates from near-zero to over 5% between 2022-2023. This compressed equity valuations, especially growth stocks, as higher discount rates reduced the present value of future earnings. The S&P 500 fell roughly 20% in 2022 before recovering in 2023."),
    ("user",      "How did the rate hikes specifically impact tech stocks versus value stocks?"),
    ("assistant", "Tech stocks, which are long-duration assets with earnings far in the future, were hit hardest — the Nasdaq fell over 33% in 2022. Value stocks, with near-term cash flows, were more resilient. Energy and financials actually outperformed during the hiking cycle."),
    ("user",      "What happened to bond markets during the same period?"),
    ("assistant", "Bond markets experienced historic losses. The Bloomberg US Aggregate Bond Index fell about 13% in 2022 — its worst year since the 1970s. The 10-year Treasury yield rose from under 2% to over 4%, causing significant mark-to-market losses for bond holders."),
    ("user",      "How did this affect bank balance sheets, particularly SVB?"),
    ("assistant", "Banks holding long-duration bonds saw unrealised losses balloon. Silicon Valley Bank had concentrated exposure to long-duration MBS and Treasuries. When it needed to sell these at a loss to cover deposits, it triggered a bank run and collapsed in March 2023."),
    ("user",      "What were the main assets and sectors we discussed, and what was the key risk theme?"),
]

SCENARIOS = [
    {
        "name": "Research: AI Enterprise Adoption",
        "domain": "research",
        "conversation": RESEARCH_CONVERSATION,
        "recall_queries": [
            "Which industries lead AI adoption?",
            "What barriers did we discuss?",
            "How do SMEs differ from large enterprises in AI adoption?",
        ],
        "expected_patterns": ["ai", "adoption", "enterprise", "barrier", "industry"],
    },
    {
        "name": "Finance: Fed Rate Hiking Cycle",
        "domain": "finance",
        "conversation": FINANCE_CONVERSATION,
        "recall_queries": [
            "What happened to tech stocks during rate hikes?",
            "How were bonds affected?",
            "What caused SVB to collapse?",
        ],
        "expected_patterns": ["fed", "rate", "bond", "svb", "tech"],
    },
]

# ── Scoring helpers ───────────────────────────────────────────────────────────

def score_recall(recalled: str, query: str, expected_keywords: list[str]) -> float:
    """
    Simple keyword overlap score 0-1 between recalled text and expected patterns.
    Also uses LLM judge for semantic relevance (0-10 scaled to 0-1).
    """
    if not recalled or (recalled.startswith("[") and "error" in recalled.lower()):
        return 0.0
    # Keyword overlap
    recalled_lower = recalled.lower()
    kw_hits = sum(1 for k in expected_keywords if k.lower() in recalled_lower)
    kw_score = kw_hits / max(len(expected_keywords), 1)
    return round(kw_score, 3)


def score_patterns(patterns: str, expected: list[str]) -> float:
    if not patterns or "error" in patterns.lower() or "No " in patterns:
        return 0.0
    hits = sum(1 for k in expected if k.lower() in patterns.lower())
    return round(hits / max(len(expected), 1), 3)


def llm_recall_score(query: str, recalled: str, conversation_summary: str) -> float:
    """Ask the LLM judge: how relevant is `recalled` to `query` given the conversation?"""
    if not recalled or (recalled.startswith("[") and "error" in recalled.lower()):
        return 0.0
    prompt = (
        f"Conversation so far:\n{conversation_summary[:800]}\n\n"
        f"Recall query: {query}\n\n"
        f"Retrieved memory:\n{recalled}\n\n"
        "Score how well the retrieved memory answers the recall query, given the conversation. "
        "Reply with ONLY a number from 0 to 10."
    )
    try:
        raw = llm_call(prompt, system="You are a memory quality evaluator. Reply with only a number 0-10.", max_tokens=10)
        import re
        match = re.search(r'\b(10|[0-9](\.[0-9]+)?)\b', raw)
        if match:
            return round(float(match.group(1)) / 10.0, 2)
        match = re.search(r'\d+', raw)
        if match:
            return round(float(match.group(0)) / 10.0, 2)
        return 0.0
    except Exception:
        return 0.0

# ── Main benchmark ────────────────────────────────────────────────────────────

def run_memory_benchmark(solutions: list, scenarios: list) -> list[dict]:
    results = []

    for solution in solutions:
        sol_result = {
            "solution": solution.name,
            "scenarios": [],
            "avg_recall_kw": 0.0,
            "avg_recall_llm": 0.0,
            "avg_pattern": 0.0,
            "avg_latency_ms": 0.0,
        }

        recall_kw_scores, recall_llm_scores, pattern_scores, latencies = [], [], [], []

        for scenario in scenarios:
            print(f"\n  [{solution.name}] Scenario: {scenario['name']}")
            session_id = f"{solution.name.replace(' ', '_')}_{scenario['name'][:10]}"
            solution.reset(session_id)

            # Feed conversation turns
            turns_text = ""
            for role, content in scenario["conversation"][:-1]:  # last turn is the recall probe
                t0 = time.perf_counter()
                solution.add(role, content, session_id=session_id)
                latencies.append((time.perf_counter() - t0) * 1000)
                turns_text += f"[{role}]: {content}\n"

            # Test recall
            recall_results = []
            for rq in scenario["recall_queries"]:
                t0 = time.perf_counter()
                recalled = solution.recall(rq, session_id=session_id)
                recall_lat = (time.perf_counter() - t0) * 1000
                latencies.append(recall_lat)

                kw_score = score_recall(recalled, rq, scenario["expected_patterns"])
                llm_score = llm_recall_score(rq, recalled, turns_text)
                recall_kw_scores.append(kw_score)
                recall_llm_scores.append(llm_score)

                recall_results.append({
                    "query": rq,
                    "recalled_snippet": recalled[:200],
                    "kw_score": kw_score,
                    "llm_score": llm_score,
                    "latency_ms": round(recall_lat, 1),
                })
                print(f"    Recall '{rq[:40]}...' -> kw={kw_score} llm={llm_score}")

            # Test pattern extraction
            t0 = time.perf_counter()
            patterns = solution.extract_patterns(session_id=session_id)
            pat_lat = (time.perf_counter() - t0) * 1000
            latencies.append(pat_lat)
            pat_score = score_patterns(patterns, scenario["expected_patterns"])
            pattern_scores.append(pat_score)

            print(f"    Patterns: {patterns[:120]}")
            print(f"    Pattern score: {pat_score}")

            sol_result["scenarios"].append({
                "scenario": scenario["name"],
                "domain": scenario["domain"],
                "recall_results": recall_results,
                "patterns": patterns[:300],
                "pattern_score": pat_score,
            })

        # Aggregate
        sol_result["avg_recall_kw"] = round(sum(recall_kw_scores) / max(len(recall_kw_scores), 1), 3)
        sol_result["avg_recall_llm"] = round(sum(recall_llm_scores) / max(len(recall_llm_scores), 1), 3)
        sol_result["avg_pattern"] = round(sum(pattern_scores) / max(len(pattern_scores), 1), 3)
        sol_result["avg_latency_ms"] = round(sum(latencies) / max(len(latencies), 1), 1)
        results.append(sol_result)

    return results


def print_summary_table(results: list[dict]):
    print("\n" + "=" * 70)
    print(f"{'Solution':<28} {'Recall(KW)':<12} {'Recall(LLM)':<13} {'Patterns':<10} {'Latency(ms)'}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['solution']:<28} {r['avg_recall_kw']:<12} {r['avg_recall_llm']:<13} "
            f"{r['avg_pattern']:<10} {r['avg_latency_ms']}"
        )
    print("=" * 70)


def main():
    from dotenv import load_dotenv
    load_dotenv()

    print("\n=== Memory Solution Benchmark ===\n")
    print("Loading solutions...")

    solutions = []

    # Always include baseline
    from memory.in_memory import InMemory
    solutions.append(InMemory())
    print("  [OK] InMemory (baseline)")

    # mem0
    try:
        from memory.mem0_memory import Mem0Memory
        solutions.append(Mem0Memory())
        print("  [OK] mem0")
    except Exception as e:
        print(f"  [skipped] mem0 skipped: {e}")

    # Zep
    try:
        from memory.zep_memory import ZepMemory
        solutions.append(ZepMemory())
        print("  [OK] Zep")
    except Exception as e:
        print(f"  [skipped] Zep skipped: {e}")

    # LangChain
    try:
        from memory.langchain_memory import LangChainMemory
        solutions.append(LangChainMemory())
        print("  [OK] LangChain SummaryBuffer")
    except Exception as e:
        print(f"  [skipped] LangChain skipped: {e}")

    print(f"\nRunning benchmark with {len(solutions)} solution(s) on {len(SCENARIOS)} scenarios...\n")

    results = run_memory_benchmark(solutions, SCENARIOS)
    print_summary_table(results)

    # Save results
    out_path = Path("results/memory_benchmark_results.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()