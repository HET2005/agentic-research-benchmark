import time
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from .base import llm_call, search_web, Timer

class P7State(TypedDict):
    question: str
    run_id: str
    seed: int
    hypothesis: str
    supporting_evidence: str
    refuting_evidence: str
    evidence_evaluation: str
    answer: str
    token_count: int
    latency: float

def node_hypothesize(state: P7State) -> dict:
    system = "You are a research scientist. Form a clear, testable hypothesis (2-3 sentences) for the question."
    hypothesis = llm_call(f"Form a hypothesis for: {state['question']}", system=system, max_tokens=150)
    return {"hypothesis": hypothesis}

def node_gather_supporting(state: P7State) -> dict:
    q = f"evidence supporting {state['hypothesis'][:80]} {state['question']}"
    return {"supporting_evidence": search_web(q, max_results=5)}

def node_gather_refuting(state: P7State) -> dict:
    q = f"evidence against challenges {state['hypothesis'][:80]} {state['question']}"
    return {"refuting_evidence": search_web(q, max_results=5)}

def node_test(state: P7State) -> dict:
    system = "You are a critical thinker. Weigh supporting and refuting evidence objectively."
    prompt = f"Hypothesis: {state['hypothesis']}\nSupporting:\n{state['supporting_evidence'][:1500]}\nRefuting:\n{state['refuting_evidence'][:1500]}\nEvaluate the evidence."
    evaluation = llm_call(prompt, system=system, max_tokens=700)
    return {"evidence_evaluation": evaluation}

def node_conclude(state: P7State) -> dict:
    system = "You are a research analyst. Draw balanced, evidence-based conclusions and write a comprehensive final answer."
    prompt = f"Question: {state['question']}\nHypothesis: {state['hypothesis']}\nEvaluation:\n{state['evidence_evaluation']}\nWrite the final comprehensive answer."
    t0 = time.perf_counter()
    answer = llm_call(prompt, system=system, max_tokens=2500)
    return {"answer": answer, "latency": time.perf_counter() - t0, "token_count": len(answer.split())}

def build_graph():
    g = StateGraph(P7State)
    g.add_node("hypothesize", node_hypothesize)
    g.add_node("gather_supporting", node_gather_supporting)
    g.add_node("gather_refuting", node_gather_refuting)
    g.add_node("test", node_test)
    g.add_node("conclude", node_conclude)
    g.add_edge(START, "hypothesize")
    g.add_edge("hypothesize", "gather_supporting")
    g.add_edge("gather_supporting", "gather_refuting")
    g.add_edge("gather_refuting", "test")
    g.add_edge("test", "conclude")
    g.add_edge("conclude", END)
    return g.compile()

def run(question: str, run_id: str = "default", seed: int = 0) -> dict:
    graph = build_graph()
    init: P7State = {"question": question, "run_id": run_id, "seed": seed,
                     "hypothesis": "", "supporting_evidence": "", "refuting_evidence": "",
                     "evidence_evaluation": "", "answer": "", "token_count": 0, "latency": 0.0}
    with Timer() as t:
        final = graph.invoke(init)
    return {"pipeline": "P7", "framework": "langgraph", "question": question,
            "hypothesis": final["hypothesis"], "answer": final["answer"],
            "latency": t.elapsed, "token_count": final.get("token_count", 0),
            "run_id": run_id, "seed": seed}