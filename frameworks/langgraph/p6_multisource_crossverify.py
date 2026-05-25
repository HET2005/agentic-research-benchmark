import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, search_finance, Timer

class P6State(TypedDict):
    question: str
    run_id: str
    seed: int
    web_results: str
    finance_results: str
    verification_report: str
    answer: str
    token_count: int
    latency: float

def node_web_retrieve(state: P6State) -> dict:
    return {"web_results": search_web(state["question"], max_results=8)}

def node_finance_retrieve(state: P6State) -> dict:
    q = state["question"].lower()
    ticker = None
    for name, t in [("nvidia","NVDA"),("apple","AAPL"),("microsoft","MSFT"),("tesla","TSLA"),
                    ("amazon","AMZN"),("google","GOOGL"),("bitcoin","BTC-USD"),("gold","GC=F")]:
        if name in q:
            ticker = t
            break
    result = search_finance(ticker or "AAPL")
    return {"finance_results": f"[Ticker: {ticker or 'N/A'}]\n{result}"}

def node_cross_verify(state: P6State) -> dict:
    system = "You are a data reconciliation expert. Compare web and financial sources. Flag conflicts. Establish a unified fact set."
    prompt = f"Question: {state['question']}\nWeb:\n{state['web_results'][:2000]}\nFinancial:\n{state['finance_results'][:1000]}\nReconcile and produce verification report."
    report = llm_call(prompt, system=system, max_tokens=700)
    return {"verification_report": report}

def node_synthesize(state: P6State) -> dict:
    system = "You are a research analyst. Write a comprehensive answer using verified cross-source data. Cite sources."
    prompt = f"Question: {state['question']}\nVerification:\n{state['verification_report']}\nWeb:\n{state['web_results'][:1500]}\nFinancial:\n{state['finance_results'][:800]}\nWrite the final answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system, max_tokens=2500)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P6State)
    g.add_node("web_retrieve", node_web_retrieve)
    g.add_node("finance_retrieve", node_finance_retrieve)
    g.add_node("cross_verify", node_cross_verify)
    g.add_node("synthesize", node_synthesize)
    g.add_edge(START, "web_retrieve")
    g.add_edge("web_retrieve", "finance_retrieve")
    g.add_edge("finance_retrieve", "cross_verify")
    g.add_edge("cross_verify", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P6State = {"question": question, "run_id": run_id, "seed": seed,
                     "web_results": "", "finance_results": "", "verification_report": "", "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P6", "framework": "langgraph", "question": question,
            "verification_report": final["verification_report"], "answer": final["answer"],
            "latency": t.elapsed, "token_count": final.get("token_count", 0),
            "run_id": run_id, "seed": seed}