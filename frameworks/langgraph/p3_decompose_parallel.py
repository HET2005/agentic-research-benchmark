import json
import time
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P3State(TypedDict):
    question: str
    run_id: str
    seed: int
    sub_queries: List[str]
    retrieved_chunks: List[str]
    answer: str
    token_count: int
    latency: float

def node_decompose(state: P3State) -> dict:
    system = "You are a research planner. Break questions into sub-questions. Return ONLY a JSON array of 4 strings."
    raw = llm_call(f"Decompose into 4 sub-questions (JSON array only): {state['question']}", system=system, max_tokens=300)
    try:
        sub_queries = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except Exception:
        lines = [l.strip().lstrip("-•1234567890. ") for l in raw.splitlines() if len(l.strip()) > 10]
        sub_queries = lines[:4] or [state["question"]]
    return {"sub_queries": sub_queries}

def node_parallel_retrieve(state: P3State) -> dict:
    chunks = []
    for i, q in enumerate(state["sub_queries"]):
        chunks.append(f"[Sub-query {i+1}: {q}]\n{search_web(q, max_results=4)}")
    return {"retrieved_chunks": chunks}

def node_merge(state: P3State) -> dict:
    system = "You are a research synthesiser. Merge information from multiple sources into one comprehensive answer. Cite as [Source N]."
    combined = "\n\n".join(state["retrieved_chunks"])
    prompt = f"Original question: {state['question']}\n\nInformation:\n{combined[:4000]}\n\nWrite a comprehensive merged answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system, max_tokens=2048)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P3State)
    g.add_node("decompose", node_decompose)
    g.add_node("parallel_retrieve", node_parallel_retrieve)
    g.add_node("merge", node_merge)
    g.add_edge(START, "decompose")
    g.add_edge("decompose", "parallel_retrieve")
    g.add_edge("parallel_retrieve", "merge")
    g.add_edge("merge", END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P3State = {"question": question, "run_id": run_id, "seed": seed,
                     "sub_queries": [], "retrieved_chunks": [], "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P3", "framework": "langgraph", "question": question,
            "sub_queries": final["sub_queries"], "answer": final["answer"],
            "latency": t.elapsed, "token_count": final.get("token_count", 0),
            "run_id": run_id, "seed": seed}