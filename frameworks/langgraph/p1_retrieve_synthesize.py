from frameworks.memory_utils import with_memory
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
    word_count: int  # FIX: Renamed from token_count
    latency: float

def node_retrieve(state: P1State) -> dict:
    return {"retrieved": search_web(state["question"], max_results=6)}

def node_synthesize(state: P1State) -> dict:
    system = "You are a rigorous research assistant. Use the search results to answer accurately. Cite sources as [Source N]."
    prompt = f"Question: {state['question']}\n\nSearch results:\n{state['retrieved']}\n\nWrite a comprehensive answer."
    t0 = time.perf_counter()
    
    # FIX: Pass the seed to the LLM to guarantee deterministic outputs!
    answer = llm_call(prompt, system=system, seed=state.get("seed"))
    
    return {"answer": answer, "latency": time.perf_counter() - t0, "word_count": len(answer.split())}

def build_graph():
    g = StateGraph(P1State)
    g.add_node("retrieve", node_retrieve)
    g.add_node("synthesize", node_synthesize)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()

@with_memory
def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P1State = {"question": question, "run_id": run_id, "seed": seed,
                     "retrieved": "", "answer": "", "word_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P1", "framework": "langgraph", "question": question,
            "answer": final["answer"], "latency": t.elapsed,
            "word_count": final.get("word_count", 0), "run_id": run_id, "seed": seed}