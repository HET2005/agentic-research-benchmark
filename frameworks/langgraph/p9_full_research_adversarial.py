import json
import time
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, search_finance, Timer

class P9State(TypedDict):
    question: str
    run_id: str
    seed: int
    sub_questions: List[str]
    web_chunks: List[str]
    finance_data: str
    cross_verify_report: str
    synthesis: str
    adversarial_critique: str
    revised_synthesis: str
    answer: str
    word_count: int
    latency: float

def node_decompose(state: P9State) -> dict:
    system = "You are a research strategist. Return ONLY a JSON array of 4 sub-question strings."
    raw = llm_call(f"Decompose into 4 sub-questions (JSON array): {state['question']}", system=system, max_tokens=300, seed=state.get("seed"))
    try:
        sub_qs = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except Exception:
        sub_qs = [state["question"]]
    return {"sub_questions": sub_qs}

def node_multi_retrieve(state: P9State) -> dict:
    chunks = [f"[Q{i+1}: {q}]\n{search_web(q, max_results=4)}" for i, q in enumerate(state["sub_questions"])]
    q = state["question"].lower()
    fin = ""
    for name, ticker in [("nvidia","NVDA"),("apple","AAPL"),("tesla","TSLA"),("bitcoin","BTC-USD"),("gold","GC=F")]:
        if name in q:
            fin = search_finance(ticker)
            break
    return {"web_chunks": chunks, "finance_data": fin}

def node_cross_verify(state: P9State) -> dict:
    system = "You are a data integrity analyst. Review sources for consistency. Flag contradictions. Establish unified facts."
    all_chunks = "\n\n".join(state["web_chunks"])
    report = llm_call(f"Question: {state['question']}\nSources:\n{all_chunks[:3000]}\nFinancial:\n{state['finance_data'][:500]}\nCross-verify.", system=system, max_tokens=700, seed=state.get("seed"))
    return {"cross_verify_report": report}

def node_synthesize(state: P9State) -> dict:
    system = "You are a research analyst. Synthesise verified information into a comprehensive answer with ## headers. Cite [Source N]."
    all_chunks = "\n\n".join(state["web_chunks"])
    synthesis = llm_call(f"Question: {state['question']}\nVerification:\n{state['cross_verify_report']}\nSources:\n{all_chunks[:3000]}\nWrite comprehensive synthesis.", system=system, max_tokens=3000, seed=state.get("seed"))
    return {"synthesis": synthesis}

def node_adversarial_critique(state: P9State) -> dict:
    system = "You are a RED TEAM agent. AGGRESSIVELY attack the draft. Find every error, gap, overstatement, missing counterargument. Be brutal and specific."
    critique = llm_call(f"ATTACK this draft for: {state['question']}\n\nDraft:\n{state['synthesis'][:2500]}", system=system, max_tokens=900, seed=state.get("seed"))
    return {"adversarial_critique": critique}

def node_revise(state: P9State) -> dict:
    system = "You are the author responding to adversarial review. Address EVERY critique point. Strengthen all weak claims."
    revised = llm_call(f"Question: {state['question']}\nDraft:\n{state['synthesis'][:2000]}\nCritique:\n{state['adversarial_critique']}\nWrite revised answer.", system=system, max_tokens=3500, seed=state.get("seed"))
    return {"revised_synthesis": revised}

def node_report(state: P9State) -> dict:
    system = "You are a professional editor. Format as a polished research report with Executive Summary and Key Conclusions."
    t0 = time.perf_counter()
    answer = llm_call(f"Format as professional report:\n{state['revised_synthesis']}", system=system, max_tokens=4000, seed=state.get("seed"))
    return {"answer": answer, "latency": time.perf_counter() - t0, "word_count": len(answer.split())}

def build_graph():
    g = StateGraph(P9State)
    nodes = [("decompose", node_decompose), ("multi_retrieve", node_multi_retrieve),
             ("cross_verify", node_cross_verify), ("synthesize", node_synthesize),
             ("adversarial_critique", node_adversarial_critique), ("revise", node_revise), ("report", node_report)]
    for name, fn in nodes:
        g.add_node(name, fn)
    order = [n for n, _ in nodes]
    g.add_edge(START, order[0])
    for a, b in zip(order, order[1:]):
        g.add_edge(a, b)
    g.add_edge(order[-1], END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P9State = {"question": question, "run_id": run_id, "seed": seed,
                     "sub_questions": [], "web_chunks": [], "finance_data": "",
                     "cross_verify_report": "", "synthesis": "", "adversarial_critique": "",
                     "revised_synthesis": "", "answer": "", "word_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P9", "framework": "langgraph", "question": question,
            "sub_questions": final["sub_questions"], "adversarial_critique": final["adversarial_critique"],
            "answer": final["answer"], "latency": t.elapsed,
            "word_count": final.get("word_count", 0), "run_id": run_id, "seed": seed}