import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P2State(TypedDict):
    question: str
    run_id: str
    seed: int
    rewritten_query: str
    retrieved: str
    answer: str
    token_count: int
    latency: float

def node_rewrite(state: P2State) -> dict:
    system = "You are a search query expert. Rewrite the question as an optimal search query. Output ONLY the query, max 15 words."
    rewritten = llm_call(f"Rewrite for search: {state['question']}", system=system, max_tokens=80).strip().strip('"')
    return {"rewritten_query": rewritten}

def node_retrieve(state: P2State) -> dict:
    return {"retrieved": search_web(state.get("rewritten_query") or state["question"], max_results=8)}

def node_answer(state: P2State) -> dict:
    system = "You are a research assistant. Answer the original question using retrieved info. Cite as [Source N]."
    prompt = f"Original question: {state['question']}\nSearch query used: {state['rewritten_query']}\n\nResults:\n{state['retrieved']}\n\nWrite a comprehensive answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P2State)
    g.add_node("rewrite", node_rewrite)
    g.add_node("retrieve", node_retrieve)
    g.add_node("answer", node_answer)
    g.add_edge(START, "rewrite")
    g.add_edge("rewrite", "retrieve")
    g.add_edge("retrieve", "answer")
    g.add_edge("answer", END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P2State = {"question": question, "run_id": run_id, "seed": seed,
                     "rewritten_query": "", "retrieved": "", "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P2", "framework": "langgraph", "question": question,
            "rewritten_query": final["rewritten_query"], "answer": final["answer"],
            "latency": t.elapsed, "token_count": final.get("token_count", 0),
            "run_id": run_id, "seed": seed}