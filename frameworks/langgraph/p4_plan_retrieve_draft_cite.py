from frameworks.memory_utils import with_memory
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P4State(TypedDict):
    question: str
    run_id: str
    seed: int
    plan: str
    retrieved: str
    draft: str
    answer: str
    word_count: int
    latency: float

def node_plan(state: P4State) -> dict:
    system = "You are a senior research analyst. Create a structured research plan with key topics, retrieval targets, and answer structure."
    plan = llm_call(f"Create a research plan for: {state['question']}", system=system, max_tokens=500, seed=state.get("seed"))
    return {"plan": plan}

def node_retrieve(state: P4State) -> dict:
    r1 = search_web(state["question"], max_results=6)
    r2 = search_web(f"{state['question']} analysis overview", max_results=4)
    return {"retrieved": r1 + "\n\n---\n\n" + r2}

def node_draft(state: P4State) -> dict:
    system = "You are a research writer. Draft a comprehensive answer following the plan. Use headers and cite as [Source N]."
    prompt = f"Question: {state['question']}\nPlan:\n{state['plan']}\nSources:\n{state['retrieved'][:3000]}\n\nWrite the full draft."
    draft = llm_call(prompt, system=system, max_tokens=2500, seed=state.get("seed"))
    return {"draft": draft}

def node_cite_check(state: P4State) -> dict:
    system = "You are a fact-checking editor. Verify citations, add missing ones from source material, flag unsupported claims. Output the final verified answer."
    prompt = f"Draft:\n{state['draft']}\n\nSource material:\n{state['retrieved'][:2000]}\n\nOutput the citation-verified final answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system, max_tokens=3000, seed=state.get("seed"))
    return {"answer": answer, "latency": time.perf_counter() - t0, "word_count": len(answer.split())}

def build_graph():
    g = StateGraph(P4State)
    g.add_node("plan", node_plan)
    g.add_node("retrieve", node_retrieve)
    g.add_node("draft", node_draft)
    g.add_node("cite_check", node_cite_check)
    g.add_edge(START, "plan")
    g.add_edge("plan", "retrieve")
    g.add_edge("retrieve", "draft")
    g.add_edge("draft", "cite_check")
    g.add_edge("cite_check", END)
    return g.compile()

@with_memory
def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P4State = {"question": question, "run_id": run_id, "seed": seed,
                     "plan": "", "retrieved": "", "draft": "", "answer": "", "word_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P4", "framework": "langgraph", "question": question,
            "plan": final["plan"], "answer": final["answer"],
            "latency": t.elapsed, "word_count": final.get("word_count", 0),
            "run_id": run_id, "seed": seed}