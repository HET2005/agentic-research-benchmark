from frameworks.memory_utils import with_memory
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P5State(TypedDict):
    question: str
    run_id: str
    seed: int
    retrieved: str
    draft: str
    critique: str
    answer: str
    word_count: int
    latency: float

def node_retrieve(state: P5State) -> dict:
    return {"retrieved": search_web(state["question"], max_results=8)}

def node_draft(state: P5State) -> dict:
    system = "You are a research analyst. Write a comprehensive answer based on retrieved information. Cite sources."
    draft = llm_call(f"Question: {state['question']}\nSources:\n{state['retrieved'][:2500]}\nWrite a comprehensive draft.", system=system, max_tokens=2000, seed=state.get("seed"))
    return {"draft": draft}

def node_self_critique(state: P5State) -> dict:
    system = "You are a critical peer reviewer. Evaluate the draft on: 1.Accuracy 2.Completeness 3.Coherence 4.Groundedness. Be specific and actionable."
    critique = llm_call(f"Question: {state['question']}\nDraft:\n{state['draft']}\nProvide detailed critique.", system=system, max_tokens=700, seed=state.get("seed"))
    return {"critique": critique}

def node_revise(state: P5State) -> dict:
    system = "You are a research editor. Revise the draft addressing every critique point. Produce the definitive final answer."
    prompt = f"Question: {state['question']}\nDraft:\n{state['draft']}\nCritique:\n{state['critique']}\nSources:\n{state['retrieved'][:1500]}\nWrite improved final answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system, max_tokens=2500, seed=state.get("seed"))
    return {"answer": answer, "latency": time.perf_counter() - t0, "word_count": len(answer.split())}

def build_graph():
    g = StateGraph(P5State)
    g.add_node("retrieve", node_retrieve)
    g.add_node("draft", node_draft)
    g.add_node("self_critique", node_self_critique)
    g.add_node("revise", node_revise)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "draft")
    g.add_edge("draft", "self_critique")
    g.add_edge("self_critique", "revise")
    g.add_edge("revise", END)
    return g.compile()

@with_memory
def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P5State = {"question": question, "run_id": run_id, "seed": seed,
                     "retrieved": "", "draft": "", "critique": "", "answer": "", "word_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P5", "framework": "langgraph", "question": question,
            "draft": final["draft"], "critique": final["critique"], "answer": final["answer"],
            "latency": t.elapsed, "word_count": final.get("word_count", 0),
            "run_id": run_id, "seed": seed}