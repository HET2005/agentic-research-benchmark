import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P10State(TypedDict):
    question: str
    run_id: str
    seed: int
    lit_scan: str
    research_gaps: str
    hypothesis: str
    framework: str
    evidence: str
    paper: str
    methodology_review: str
    clarity_review: str
    evidence_review: str
    revised_paper: str
    answer: str
    token_count: int
    latency: float

def node_lit_scan(state: P10State) -> dict:
    r1 = search_web(state["question"], max_results=6)
    r2 = search_web(f"{state['question']} research review", max_results=4)
    return {"lit_scan": r1 + "\n\n---\n\n" + r2}

def node_identify_gaps(state: P10State) -> dict:
    system = "You are a research director. Identify what is well-understood, contested, and what gaps remain."
    gaps = llm_call(f"Topic: {state['question']}\nLiterature:\n{state['lit_scan'][:2000]}\nIdentify research gaps.", system=system, max_tokens=500)
    return {"research_gaps": gaps}

def node_hypothesize(state: P10State) -> dict:
    system = "You are a research scientist. Form a novel testable hypothesis (2-3 sentences) addressing the gaps."
    hypothesis = llm_call(f"Topic: {state['question']}\nGaps:\n{state['research_gaps']}\nForm hypothesis.", system=system, max_tokens=200)
    return {"hypothesis": hypothesis}

def node_design(state: P10State) -> dict:
    system = "You are a methodology expert. Design an analytical framework for investigating the hypothesis."
    fw = llm_call(f"Hypothesis: {state['hypothesis']}\nDesign analytical framework.", system=system, max_tokens=400)
    return {"framework": fw}

def node_execute(state: P10State) -> dict:
    queries_raw = llm_call(f"Hypothesis: {state['hypothesis']}\nList 3 search queries (one per line).", system="You are a search strategist.", max_tokens=150)
    queries = [l.strip().lstrip("-123456789. ") for l in queries_raw.splitlines() if len(l.strip()) > 8][:3]
    evidence = "\n\n".join(search_web(q, max_results=4) for q in (queries or [state["question"]]))
    return {"evidence": evidence}

def node_write_paper(state: P10State) -> dict:
    system = "You are an academic writer. Write a full research paper with Abstract, Introduction, Analysis, Discussion, Conclusion sections using ## headers."
    paper = llm_call(f"Topic: {state['question']}\nHypothesis: {state['hypothesis']}\nFramework: {state['framework']}\nEvidence:\n{state['evidence'][:3000]}\nWrite full paper.", system=system, max_tokens=4000)
    return {"paper": paper}

def node_methodology_review(state: P10State) -> dict:
    system = "You are Reviewer 1 (Methodology). Give 3-5 numbered methodology recommendations."
    return {"methodology_review": llm_call(f"Paper:\n{state['paper'][:2500]}\nMethodology review:", system=system, max_tokens=500)}

def node_clarity_review(state: P10State) -> dict:
    system = "You are Reviewer 2 (Clarity). Give 3-5 numbered clarity and structure recommendations."
    return {"clarity_review": llm_call(f"Paper:\n{state['paper'][:2500]}\nClarity review:", system=system, max_tokens=500)}

def node_evidence_review(state: P10State) -> dict:
    system = "You are Reviewer 3 (Evidence). Give 3-5 numbered evidence quality recommendations."
    return {"evidence_review": llm_call(f"Paper:\n{state['paper'][:2500]}\nEvidence review:", system=system, max_tokens=500)}

def node_revise(state: P10State) -> dict:
    system = "You are the paper author. Address ALL reviewer recommendations comprehensively."
    revised = llm_call(
        f"Paper:\n{state['paper'][:2000]}\nR1:\n{state['methodology_review']}\nR2:\n{state['clarity_review']}\nR3:\n{state['evidence_review']}\nWrite revised paper.",
        system=system, max_tokens=4000)
    return {"revised_paper": revised}

def node_publish(state: P10State) -> dict:
    system = "You are a journal editor. Final copy-edit. Ensure structured abstract is present."
    t0 = time.perf_counter()
    answer = llm_call(f"Final edit:\n{state['revised_paper']}", system=system, max_tokens=4500)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P10State)
    nodes = [
        ("lit_scan", node_lit_scan), ("identify_gaps", node_identify_gaps),
        ("hypothesize", node_hypothesize), ("design", node_design),
        ("execute", node_execute), ("write_paper", node_write_paper),
        ("methodology_review", node_methodology_review), ("clarity_review", node_clarity_review),
        ("evidence_review", node_evidence_review), ("revise", node_revise), ("publish", node_publish),
    ]
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
    init: P10State = {"question": question, "run_id": run_id, "seed": seed,
                      "lit_scan": "", "research_gaps": "", "hypothesis": "", "framework": "",
                      "evidence": "", "paper": "", "methodology_review": "", "clarity_review": "",
                      "evidence_review": "", "revised_paper": "", "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P10", "framework": "langgraph", "question": question,
            "hypothesis": final["hypothesis"], "answer": final["answer"],
            "latency": t.elapsed, "token_count": final.get("token_count", 0),
            "run_id": run_id, "seed": seed}