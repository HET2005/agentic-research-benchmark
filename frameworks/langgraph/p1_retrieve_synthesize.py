import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P1State(TypedDict):
    question: str
    run_id: str
    seed: int
    retrieved: str
    answer: str
    token_count: int
    latency: float

def node_retrieve(state: P1State) -> dict:
    return {"retrieved": search_web(state["question"], max_results=6)}

def node_synthesize(state: P1State) -> dict:
    system = "You are a rigorous research assistant. Use the search results to answer accurately. Cite sources as [Source N]."
    prompt = f"Question: {state['question']}\n\nSearch results:\n{state['retrieved']}\n\nWrite a comprehensive answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P1State)
    g.add_node("retrieve", node_retrieve)
    g.add_node("synthesize", node_synthesize)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P1State = {"question": question, "run_id": run_id, "seed": seed,
                     "retrieved": "", "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P1", "framework": "langgraph", "question": question,
            "answer": final["answer"], "latency": t.elapsed,
            "token_count": final.get("token_count", 0), "run_id": run_id, "seed": seed}