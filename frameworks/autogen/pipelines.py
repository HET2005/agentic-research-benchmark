"""
AutoGen implementations of all 10 pipelines.
Uses conversational multi-agent pattern via simulated turns.
"""

import json
from .base import llm_call, web_search, finance_search, Timer, conversation_turn, result_dict


# ── P1: Retrieve → Synthesize ─────────────────────────────────────────────────

def run_p1(question: str, run_id: str = "default", seed: int = 0) -> dict:
    retriever_sys = "You are a web research agent. Search and summarise relevant information."
    synthesiser_sys = "You are a synthesis agent. Write comprehensive, cited research answers."

    retrieved = web_search(question, max_results=6)
    turn1 = conversation_turn(
        f"I retrieved this for the question '{question}':\n{retrieved[:2000]}\nSummarise key points.",
        retriever_sys
    )
    answer_prompt = (
        f"Question: {question}\nResearcher summary: {turn1}\n"
        "Write the final comprehensive answer with citations as [Source N]."
    )
    with Timer() as t:
        answer = llm_call(answer_prompt, system=synthesiser_sys, max_tokens=2000)
    return result_dict("P1", question, answer, t.elapsed, run_id, seed)


# ── P2: Query Rewrite → Retrieve → Answer ────────────────────────────────────

def run_p2(question: str, run_id: str = "default", seed: int = 0) -> dict:
    rewriter_sys = "You are a query optimisation agent. Rewrite questions as optimal search queries. Output ONLY the query."
    researcher_sys = "You are a web research agent."
    writer_sys = "You are a research writing agent. Write comprehensive cited answers."

    rewritten = llm_call(
        f"Rewrite for search (max 12 words): {question}",
        system=rewriter_sys, max_tokens=80
    ).strip().strip('"')

    retrieved = web_search(rewritten or question, max_results=8)

    answer_prompt = (
        f"Original question: {question}\n"
        f"Search used: {rewritten}\n"
        f"Results:\n{retrieved[:2500]}\n\n"
        "Write the final comprehensive answer."
    )
    with Timer() as t:
        answer = llm_call(answer_prompt, system=writer_sys, max_tokens=2000)
    return result_dict("P2", question, answer, t.elapsed, run_id, seed, rewritten_query=rewritten)


# ── P3: Decompose → Parallel Retrieve → Merge ────────────────────────────────

def run_p3(question: str, run_id: str = "default", seed: int = 0) -> dict:
    planner_sys = "You are a research planner. Decompose questions into sub-questions. Return JSON array only."
    researcher_sys = "You are a multi-thread researcher."
    merger_sys = "You are a synthesis agent. Merge multiple research threads into one answer."

    raw = llm_call(
        f'Decompose into 4 sub-questions (JSON array): {question}',
        system=planner_sys, max_tokens=300
    )
    try:
        sub_qs = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except Exception:
        sub_qs = [question]

    chunks = []
    for i, q in enumerate(sub_qs[:4]):
        r = web_search(q, max_results=4)
        chunks.append(f"[Thread {i+1}: {q}]\n{r}")

    merge_prompt = (
        f"Original question: {question}\n\n"
        f"Research threads:\n{''.join(chunks)[:4000]}\n\n"
        "Merge into one comprehensive answer. Cite sources as [Source N]."
    )
    with Timer() as t:
        answer = llm_call(merge_prompt, system=merger_sys, max_tokens=2500)
    return result_dict("P3", question, answer, t.elapsed, run_id, seed, sub_questions=sub_qs)


# ── P4: Plan → Retrieve → Draft → Cite-check ─────────────────────────────────

def run_p4(question: str, run_id: str = "default", seed: int = 0) -> dict:
    planner_sys = "You are a research planning agent. Create structured research plans."
    researcher_sys = "You are a retrieval agent."
    writer_sys = "You are a drafting agent."
    checker_sys = "You are a citation verification agent. Verify claims have sources. Output final answer."

    history = []
    plan = conversation_turn(
        f"Create a research plan for: {question}",
        planner_sys, history
    )
    history.append({"role": "Planner", "content": plan})

    retrieved = web_search(question, max_results=8)
    retrieved2 = web_search(f"{question} analysis data", max_results=4)
    all_retrieved = retrieved + "\n\n" + retrieved2

    draft_prompt = (
        f"Plan:\n{plan}\n\nSources:\n{all_retrieved[:3000]}\n\n"
        f"Draft answer to: {question}"
    )
    draft = llm_call(draft_prompt, system=writer_sys, max_tokens=2500)
    history.append({"role": "Writer", "content": draft})

    check_prompt = (
        f"Draft:\n{draft[:2000]}\n\nSources available:\n{all_retrieved[:1500]}\n\n"
        "Verify citations. Add missing ones. Output the final verified answer."
    )
    with Timer() as t:
        answer = llm_call(check_prompt, system=checker_sys, max_tokens=3000)
    return result_dict("P4", question, answer, t.elapsed, run_id, seed, plan=plan)


# ── P5: Retrieve → Draft → Self-critique → Revise ────────────────────────────

def run_p5(question: str, run_id: str = "default", seed: int = 0) -> dict:
    writer_sys = "You are a research drafting agent."
    critic_sys = (
        "You are a critical review agent. Evaluate on: "
        "Accuracy, Completeness, Coherence, Groundedness. Be specific."
    )
    editor_sys = "You are a revision agent. Improve drafts based on critique."

    retrieved = web_search(question, max_results=8)
    draft = llm_call(
        f"Question: {question}\nSources:\n{retrieved[:2500]}\nWrite draft answer.",
        system=writer_sys, max_tokens=2000
    )
    critique = llm_call(
        f"Question: {question}\nDraft:\n{draft[:2000]}\nCritique on all 4 dimensions.",
        system=critic_sys, max_tokens=800
    )
    with Timer() as t:
        answer = llm_call(
            f"Question: {question}\nDraft:\n{draft[:1500]}\nCritique:\n{critique}\n"
            f"Sources:\n{retrieved[:1000]}\nWrite improved final answer.",
            system=editor_sys, max_tokens=2500
        )
    return result_dict("P5", question, answer, t.elapsed, run_id, seed,
                       draft=draft, critique=critique)


# ── P6: Multi-source → Cross-verify → Synthesize ─────────────────────────────

def run_p6(question: str, run_id: str = "default", seed: int = 0) -> dict:
    verifier_sys = "You are a data reconciliation agent. Compare sources, flag conflicts."
    synthesiser_sys = "You are a synthesis agent using verified cross-source data."

    web = web_search(question, max_results=8)

    q_lower = question.lower()
    fin_data = ""
    for name, ticker in [("nvidia","NVDA"),("apple","AAPL"),("microsoft","MSFT"),
                          ("tesla","TSLA"),("bitcoin","BTC-USD"),("gold","GC=F")]:
        if name in q_lower:
            fin_data = finance_search(ticker)
            break

    verify_prompt = (
        f"Question: {question}\nWeb:\n{web[:2000]}\nFinancial:\n{fin_data[:800]}\n"
        "Compare sources. Flag conflicts. Establish unified facts."
    )
    verification = llm_call(verify_prompt, system=verifier_sys, max_tokens=700)

    synth_prompt = (
        f"Question: {question}\nVerification:\n{verification}\n"
        f"Web context:\n{web[:1500]}\nWrite comprehensive cross-verified answer."
    )
    with Timer() as t:
        answer = llm_call(synth_prompt, system=synthesiser_sys, max_tokens=2500)
    return result_dict("P6", question, answer, t.elapsed, run_id, seed,
                       verification_report=verification)


# ── P7: Hypothesize → Evidence → Test → Conclude ─────────────────────────────

def run_p7(question: str, run_id: str = "default", seed: int = 0) -> dict:
    sci_sys = "You are a hypothesis formation agent. Output a clear 2-sentence hypothesis only."
    eval_sys = "You are an evidence evaluation agent. Weigh pros and cons objectively."
    conclude_sys = "You are a conclusion agent. Draw balanced, evidence-based conclusions."

    hypothesis = llm_call(f"Form a hypothesis for: {question}", system=sci_sys, max_tokens=150)
    supporting = web_search(f"evidence supporting {hypothesis[:80]} {question}", max_results=5)
    refuting = web_search(f"evidence against challenges {hypothesis[:80]} {question}", max_results=5)

    eval_prompt = (
        f"Hypothesis: {hypothesis}\n"
        f"Supporting:\n{supporting[:1500]}\nRefuting:\n{refuting[:1500]}\n"
        "Evaluate evidence for and against."
    )
    evaluation = llm_call(eval_prompt, system=eval_sys, max_tokens=700)

    conclude_prompt = (
        f"Question: {question}\nHypothesis: {hypothesis}\n"
        f"Evaluation:\n{evaluation}\nWrite final comprehensive answer."
    )
    with Timer() as t:
        answer = llm_call(conclude_prompt, system=conclude_sys, max_tokens=2500)
    return result_dict("P7", question, answer, t.elapsed, run_id, seed,
                       hypothesis=hypothesis, evaluation=evaluation)


# ── P8: Outline → Section Retrieve → Draft → Critique → Revise → Final ───────

def run_p8(question: str, run_id: str = "default", seed: int = 0) -> dict:
    outline_sys = "You are an outline agent. Return JSON array of 5 section titles only."
    writer_sys = "You are a long-form research writer. Use ## headers."
    critic_sys = "You are a peer reviewer. Give numbered critique on accuracy, completeness, coherence."
    editor_sys = "You are a revision editor. Address all critique points."
    polish_sys = "You are a copy editor. Polish to publication quality. Add executive summary."

    raw_outline = llm_call(
        f'Create 5-section outline as JSON array for: {question}',
        system=outline_sys, max_tokens=250
    )
    try:
        sections = json.loads(raw_outline[raw_outline.find("["):raw_outline.rfind("]")+1])
    except Exception:
        sections = ["Introduction", "Main Analysis", "Evidence", "Implications", "Conclusion"]

    chunks = []
    for s in sections:
        r = web_search(f"{question} — {s}", max_results=3)
        chunks.append(f"=== {s} ===\n{r}")

    draft = llm_call(
        f"Question: {question}\nOutline: {sections}\nSources:\n{''.join(chunks)[:4000]}\n"
        "Write full document with ## headers. Cite [Source N].",
        system=writer_sys, max_tokens=3500
    )
    critique = llm_call(
        f"Review this document on accuracy/completeness/coherence:\n{draft[:2500]}",
        system=critic_sys, max_tokens=800
    )
    revised = llm_call(
        f"Original:\n{draft[:2500]}\nCritique:\n{critique}\nWrite revised document.",
        system=editor_sys, max_tokens=3500
    )
    with Timer() as t:
        answer = llm_call(
            f"Polish and add executive summary:\n{revised}",
            system=polish_sys, max_tokens=4000
        )
    return result_dict("P8", question, answer, t.elapsed, run_id, seed,
                       outline=str(sections), critique=critique)


# ── P9: Full Research Loop with Adversarial Critique ─────────────────────────

def run_p9(question: str, run_id: str = "default", seed: int = 0) -> dict:
    decomp_sys = "You are a decomposition agent. Return JSON array of 4 sub-questions."
    synth_sys = "You are a synthesis agent."
    redteam_sys = (
        "You are a RED TEAM agent. Aggressively find EVERY flaw: "
        "errors, gaps, overstatements, missing counterarguments. Be brutal and specific."
    )
    reviser_sys = "You are a revision agent. Address ALL red-team critique points."
    reporter_sys = "You are a report formatter. Add Executive Summary and Key Conclusions."

    raw = llm_call(f'Decompose into 4 sub-questions (JSON array): {question}',
                   system=decomp_sys, max_tokens=300)
    try:
        sub_qs = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except Exception:
        sub_qs = [question]

    chunks = []
    for i, q in enumerate(sub_qs[:4]):
        chunks.append(f"[Q{i+1}: {q}]\n{web_search(q, max_results=4)}")

    q_lower = question.lower()
    fin = ""
    for name, ticker in [("nvidia","NVDA"),("apple","AAPL"),("tesla","TSLA"),
                          ("bitcoin","BTC-USD"),("gold","GC=F")]:
        if name in q_lower:
            fin = finance_search(ticker)
            break

    all_data = "\n\n".join(chunks) + (f"\n\nFinancial data:\n{fin}" if fin else "")

    synthesis = llm_call(
        f"Question: {question}\nSources:\n{all_data[:4000]}\n"
        "Write comprehensive synthesis with ## headers and citations.",
        system=synth_sys, max_tokens=3000
    )
    red_team = llm_call(
        f"ATTACK this draft for: {question}\n\nDraft:\n{synthesis[:2500]}\n"
        "Find every flaw. Be brutal.",
        system=redteam_sys, max_tokens=900
    )
    revised = llm_call(
        f"Question: {question}\nDraft:\n{synthesis[:2000]}\n"
        f"Red-team critique:\n{red_team}\nRevise addressing ALL points.",
        system=reviser_sys, max_tokens=3500
    )
    with Timer() as t:
        answer = llm_call(
            f"Format as professional report with Executive Summary and Key Conclusions:\n{revised}",
            system=reporter_sys, max_tokens=4000
        )
    return result_dict("P9", question, answer, t.elapsed, run_id, seed,
                       sub_questions=sub_qs, red_team_critique=red_team)


# ── P10: Academic Workflow with Multi-agent Peer Review ───────────────────────

def run_p10(question: str, run_id: str = "default", seed: int = 0) -> dict:
    lit_sys = "You are a literature review agent."
    gap_sys = "You are a research gap analyst. Identify what is known, unknown, contested."
    hyp_sys = "You are a hypothesis designer. Form a novel testable hypothesis (2-3 sentences)."
    method_sys = "You are a methodology designer. Design an analytical framework."
    writer_sys = "You are an academic paper writer. Use Abstract/Intro/Analysis/Discussion/Conclusion."
    rev1_sys = "You are Reviewer 1 (Methodology). Give 3-5 numbered methodology recommendations."
    rev2_sys = "You are Reviewer 2 (Clarity). Give 3-5 numbered clarity recommendations."
    rev3_sys = "You are Reviewer 3 (Evidence). Give 3-5 numbered evidence recommendations."
    reviser_sys = "You are the paper author. Address ALL reviewer recommendations."
    publisher_sys = "You are a journal editor. Final copy-edit. Ensure structured abstract present."

    lit = web_search(question, max_results=6)
    lit += "\n\n" + web_search(f"{question} research review", max_results=4)

    gaps = llm_call(f"Literature:\n{lit[:2000]}\nTopic: {question}\nIdentify gaps.",
                    system=gap_sys, max_tokens=500)
    hypothesis = llm_call(f"Gaps:\n{gaps}\nTopic: {question}\nForm research hypothesis.",
                          system=hyp_sys, max_tokens=200)
    framework = llm_call(f"Hypothesis: {hypothesis}\nDesign analytical framework.",
                         system=method_sys, max_tokens=500)

    queries_raw = llm_call(
        f"Hypothesis: {hypothesis}\nFramework: {framework[:300]}\n"
        "List 3 search queries (one per line).",
        system="You are a search strategist.", max_tokens=150
    )
    queries = [l.strip().lstrip("-123456789. ") for l in queries_raw.splitlines() if len(l.strip()) > 8][:3]
    evidence = "\n\n".join(web_search(q, max_results=4) for q in (queries or [question]))

    paper = llm_call(
        f"Topic: {question}\nHypothesis: {hypothesis}\nFramework: {framework}\n"
        f"Evidence:\n{evidence[:3000]}\nWrite full academic paper.",
        system=writer_sys, max_tokens=4000
    )
    r1 = llm_call(f"Paper:\n{paper[:2500]}\nMethodology review (numbered):", system=rev1_sys, max_tokens=500)
    r2 = llm_call(f"Paper:\n{paper[:2500]}\nClarity review (numbered):", system=rev2_sys, max_tokens=500)
    r3 = llm_call(f"Paper:\n{paper[:2500]}\nEvidence review (numbered):", system=rev3_sys, max_tokens=500)

    revised = llm_call(
        f"Paper:\n{paper[:2000]}\nR1:\n{r1}\nR2:\n{r2}\nR3:\n{r3}\n"
        "Revise addressing ALL reviewer comments.",
        system=reviser_sys, max_tokens=4000
    )
    with Timer() as t:
        answer = llm_call(
            f"Final copy-edit. Ensure structured abstract:\n{revised}",
            system=publisher_sys, max_tokens=4500
        )
    return result_dict("P10", question, answer, t.elapsed, run_id, seed,
                       hypothesis=hypothesis, reviews={"r1": r1, "r2": r2, "r3": r3})