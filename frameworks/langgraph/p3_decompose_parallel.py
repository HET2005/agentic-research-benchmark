from frameworks.memory_utils import with_memory
import json
import time
from typing import TypedDict, List
from concurrent.futures import ThreadPoolExecutor
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P3State(TypedDict):
    question: str
    run_id: str
    seed: int
    sub_queries: List[str]
    retrieved_chunks: List[str]
    answer: str
    word_count: int
    latency: float

def node_decompose(state: P3State) -> dict:
    system = "You are a research planner. Break questions into sub-questions. Return ONLY a JSON array of 4 strings."
    prompt = f"Decompose into 4 sub-questions (JSON array only): {state['question']}"
    if state["seed"] > 0:
        prompt += f"\n\n[Seed variation: {state['seed']}]"
        
    raw = llm_call(prompt, system=system, max_tokens=300, seed=state.get("seed"))
    try:
        sub_queries = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except Exception:
        lines = [l.strip().lstrip("-•1234567890. ") for l in raw.splitlines() if len(l.strip()) > 10]
        sub_queries = lines[:4] or [state["question"]]
    return {"sub_queries": sub_queries}

def node_parallel_retrieve(state: P3State) -> dict:
    chunks = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        def fetch(q_enum):
            idx, q = q_enum
            return f"[Sub-query {idx+1}: {q}]\n{search_web(q, max_results=4)}"
        
        results = executor.map(fetch, enumerate(state["sub_queries"]))
        chunks = list(results)
    return {"retrieved_chunks": chunks}

def node_merge(state: P3State) -> dict:
    system = "You are a research synthesiser. Merge information from multiple sources into one comprehensive answer. Cite as [Source N]."
    combined = "\n\n".join(state["retrieved_chunks"])
    
    prompt = f"Original question: {state['question']}\n\nInformation:\n{combined[:4000]}\n\nWrite a comprehensive merged answer."
    if state["seed"] > 0:
        prompt += f"\n\n[Seed variation: {state['seed']}]"
        
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system, max_tokens=2048, seed=state.get("seed"))
    return {"answer": answer, "latency": time.perf_counter() - t0, "word_count": len(answer.split())}

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

@with_memory
def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P3State = {"question": question, "run_id": run_id, "seed": seed,
                     "sub_queries": [], "retrieved_chunks": [], "answer": "", "word_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P3", "framework": "langgraph", "question": question,
            "sub_queries": final["sub_queries"], "answer": final["answer"],
            "latency": t.elapsed, "word_count": final.get("word_count", 0),
            "run_id": run_id, "seed": seed}