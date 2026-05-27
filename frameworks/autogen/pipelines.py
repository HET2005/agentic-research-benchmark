# frameworks/autogen/pipelines.py
import os
import json
import autogen
from .base import web_search, finance_search, result_dict

def get_llm_config(seed: int):
    config_list = []
    if os.environ.get("OPENAI_API_KEY"): config_list.append({"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_API_KEY"]})
    if os.environ.get("GROQ_API_KEY"): config_list.append({"model": "llama-3.1-8b-instant", "api_key": os.environ["GROQ_API_KEY"], "api_type": "groq"})
    return {"config_list": config_list, "cache_seed": seed, "temperature": 0.7} if config_list else {"config_list": [{"model": "mock", "api_key": "mock"}]}

def run_multi_agent(question: str, agents_dict: dict, sequence: list, seed: int) -> str:
    llm_config = get_llm_config(seed)
    user = autogen.UserProxyAgent("User", human_input_mode="NEVER", code_execution_config=False)
    agents = {name: autogen.AssistantAgent(name, system_message=sys, llm_config=llm_config) for name, sys in agents_dict.items()}
    
    last_msg = f"Task: {question}"
    for idx, (agent_name, prompt_addition) in enumerate(sequence):
        user.initiate_chat(agents[agent_name], message=f"{last_msg}\n{prompt_addition}", max_turns=1, summary_method="last_msg")
        last_msg = user.last_message()["content"]
    return last_msg

def run_p1(question: str, run_id: str = "default", seed: int = 0) -> dict:
    retrieved = web_search(question)
    agents = {"Synthesizer": "You are a synthesis agent. Write comprehensive, cited research answers."}
    seq = [("Synthesizer", f"Context: {retrieved}\nWrite final answer.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P1", question, answer, 0, run_id, seed)

def run_p2(question: str, run_id: str = "default", seed: int = 0) -> dict:
    agents = {"Rewriter": "Rewrite questions as optimal search queries. Output ONLY the query.", 
              "Writer": "Write comprehensive cited answers."}
    rewritten = run_multi_agent(question, {"Rewriter": agents["Rewriter"]}, [("Rewriter", "Rewrite for search.")], seed).strip('"')
    retrieved = web_search(rewritten or question)
    answer = run_multi_agent(question, {"Writer": agents["Writer"]}, [("Writer", f"Search used: {rewritten}\nResults: {retrieved}\nWrite final answer.")], seed)
    return result_dict("P2", question, answer, 0, run_id, seed)

def run_p3(question: str, run_id: str = "default", seed: int = 0) -> dict:
    planner_out = run_multi_agent(question, {"Planner": "Decompose into 4 sub-questions. Return JSON array only."}, [("Planner", "Decompose.")], seed)
    try: sub_qs = json.loads(planner_out[planner_out.find("["):planner_out.rfind("]")+1])
    except: sub_qs = [question]
    threads = "\n".join([f"Q: {q}\nA: {web_search(q, 3)}" for q in sub_qs[:4]])
    answer = run_multi_agent(question, {"Merger": "Merge multiple research threads into one answer."}, [("Merger", f"Threads: {threads}\nMerge them.")], seed)
    return result_dict("P3", question, answer, 0, run_id, seed)

def run_p4(question: str, run_id: str = "default", seed: int = 0) -> dict:
    retrieved = web_search(question, 8)
    agents = {"Planner": "Create structured research plans.", "Writer": "Draft answer.", "Checker": "Verify claims have sources."}
    seq = [("Planner", "Create plan."), ("Writer", f"Sources: {retrieved}\nDraft answer."), ("Checker", "Verify citations and output final.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P4", question, answer, 0, run_id, seed)

def run_p5(question: str, run_id: str = "default", seed: int = 0) -> dict:
    retrieved = web_search(question, 8)
    agents = {"Writer": "Draft answer.", "Critic": "Evaluate Accuracy, Completeness, Coherence, Groundedness.", "Editor": "Improve drafts based on critique."}
    seq = [("Writer", f"Sources: {retrieved}\nDraft answer."), ("Critic", "Critique draft."), ("Editor", f"Sources: {retrieved}\nImprove final answer.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P5", question, answer, 0, run_id, seed)

def run_p6(question: str, run_id: str = "default", seed: int = 0) -> dict:
    web = web_search(question, 6)
    fin = finance_search("AAPL") if "apple" in question.lower() else ""
    agents = {"Verifier": "Compare sources, flag conflicts.", "Synthesizer": "Write cross-verified answer."}
    seq = [("Verifier", f"Web: {web}\nFin: {fin}\nEstablish facts."), ("Synthesizer", "Write comprehensive answer.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P6", question, answer, 0, run_id, seed)

def run_p7(question: str, run_id: str = "default", seed: int = 0) -> dict:
    agents = {"Hypothesizer": "Output clear hypothesis.", "Evaluator": "Weigh evidence objectively.", "Concluder": "Draw balanced conclusion."}
    hyp = run_multi_agent(question, {"H": agents["Hypothesizer"]}, [("H", "Form hypothesis.")], seed)
    evidence = web_search(f"{hyp} evidence", 8)
    answer = run_multi_agent(question, agents, [("Evaluator", f"Hypothesis: {hyp}\nEv: {evidence}\nEvaluate."), ("Concluder", "Output final conclusion.")], seed)
    return result_dict("P7", question, answer, 0, run_id, seed)

def run_p8(question: str, run_id: str = "default", seed: int = 0) -> dict:
    agents = {"Writer": "Long form research writer.", "Critic": "Peer reviewer.", "Editor": "Polished publisher."}
    sources = web_search(question, 8)
    seq = [("Writer", f"Sources: {sources}\nDraft document."), ("Critic", "Critique document."), ("Editor", "Revise and polish to publication quality.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P8", question, answer, 0, run_id, seed)

def run_p9(question: str, run_id: str = "default", seed: int = 0) -> dict:
    sources = web_search(question, 8)
    agents = {"Synth": "Synthesis agent.", "RedTeam": "Aggressively find every flaw. Be brutal.", "Reviser": "Format professional report."}
    seq = [("Synth", f"Sources: {sources}\nDraft."), ("RedTeam", "ATTACK this draft."), ("Reviser", "Fix flaws. Add Exec Summary.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P9", question, answer, 0, run_id, seed)

def run_p10(question: str, run_id: str = "default", seed: int = 0) -> dict:
    sources = web_search(question, 10)
    agents = {"Author": "Academic paper writer.", "ReviewerBoard": "Provide methodology, clarity, and evidence review.", "Editor": "Final copy-edit."}
    seq = [("Author", f"Sources: {sources}\nWrite paper."), ("ReviewerBoard", "Provide combined critique."), ("Editor", "Address critique and finalize abstract.")]
    answer = run_multi_agent(question, agents, seq, seed)
    return result_dict("P10", question, answer, 0, run_id, seed)