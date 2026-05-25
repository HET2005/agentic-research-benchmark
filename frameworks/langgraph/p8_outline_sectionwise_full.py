import json
import time
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P8State(TypedDict):
    question: str
    run_id: str
    seed: int
    sections: List[str]
    section_retrievals: List[str]
    draft: str
    critique: str
    revised_draft: str
    answer: str
    token_count: int
    latency: float

def node_outline(state: P8State) -> dict:
    system = "You are a research editor. Return ONLY a JSON array of 5 section title strings."
    raw = llm_call(f"Create 5-section outline as JSON array for: {state['question']}", system=system, max_tokens=250)
    try:
        sections = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except Exception:
        sections = ["Introduction", "Main Analysis", "Evidence and Data", "Implications", "Conclusion"]
    return {"sections": sections}

def node_section_retrieve(state: P8State) -> dict:
    retrievals = []
    for s in state["sections"]:
        r = search_web(f"{state['question']} — {s}", max_results=3)
        retrievals.append(f"=== {s} ===\n{r}")
    return {"section_retrievals": retrievals}

def node_draft(state: P8State) -> dict:
    system = "You are a research writer. Write a full document with ## headers following the outline. Cite [Source N]."
    combined = "\n\n".join(state["section_retrievals"])
    draft = llm_call(f"Question: {state['question']}\nOutline: {state['sections']}\nSources:\n{combined[:4000]}\nWrite the full document.", system=system, max_tokens=3500)
    return {"draft": draft}

def node_critique(state: P8State) -> dict:
    system = "You are a peer reviewer. Evaluate: accuracy, completeness, groundedness, coherence. Give numbered feedback."
    critique = llm_call(f"Review this document:\n{state['draft'][:2500]}", system=system, max_tokens=800)
    return {"critique": critique}

def node_revise(state: P8State) -> dict:
    system = "You are a revision editor. Improve the document addressing all critique points."
    revised = llm_call(f"Original:\n{state['draft'][:2500]}\nCritique:\n{state['critique']}\nWrite revised document.", system=system, max_tokens=3500)
    return {"revised_draft": revised}

def node_final_edit(state: P8State) -> dict:
    system = "You are a copy editor. Polish to publication quality. Add executive summary and key takeaways."
    t0 = time.perf_counter()
    answer = llm_call(f"Polish this document:\n{state['revised_draft']}", system=system, max_tokens=4000)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P8State)
    for name, fn in [("outline", node_outline), ("section_retrieve", node_section_retrieve),
                     ("draft", node_draft), ("critique", node_critique),
                     ("revise", node_revise), ("final_edit", node_final_edit)]:
        g.add_node(name, fn)
    g.add_edge(START, "outline")
    g.add_edge("outline", "section_retrieve")
    g.add_edge("section_retrieve", "draft")
    g.add_edge("draft", "critique")
    g.add_edge("critique", "revise")
    g.add_edge("revise", "final_edit")
    g.add_edge("final_edit", END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P8State = {"question": question, "run_id": run_id, "seed": seed,
                     "sections": [], "section_retrievals": [], "draft": "", "critique": "",
                     "revised_draft": "", "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P8", "framework": "langgraph", "question": question,
            "outline": final["sections"], "answer": final["answer"],
            "latency": t.elapsed, "token_count": final.get("token_count", 0),
            "run_id": run_id, "seed": seed}