"""
frameworks/crewai/p6_p10_pipelines.py
CrewAI implementations of P6 through P10 (Medium and Long tier).
"""
import os
import time
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-dummy-not-used")
os.environ["CREWAI_TRACING_ENABLED"] = "false"

from crewai import Crew, Process
from .base import WEB_TOOL, FINANCE_TOOL, make_agent, make_task, run_crew, Timer, get_llm, _mock_run
_LLM = None


def _llm():
    global _LLM
    if _LLM is None:
        _LLM = get_llm()
    return _LLM


# ══════════════════════════════════════════════════════════════════════════════
# P6: Multi-source Retrieve → Cross-verify → Synthesize
# ══════════════════════════════════════════════════════════════════════════════

def run_p6(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = _llm()
    web_researcher = make_agent(
        role="Web Research Analyst",
        goal="Retrieve comprehensive web-based information on research topics.",
        backstory="Expert at finding and evaluating online sources across multiple domains.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    finance_analyst = make_agent(
        role="Financial Data Analyst",
        goal="Retrieve structured financial market data including prices, metrics, and fundamentals.",
        backstory="Expert at financial data retrieval and quantitative analysis.",
        tools=[FINANCE_TOOL],
        llm=llm,
    )
    verifier = make_agent(
        role="Data Reconciliation Expert",
        goal="Compare information from multiple sources, identify conflicts, and establish ground truth.",
        backstory="Specialist in cross-source verification and data reconciliation.",
        tools=[],
        llm=llm,
    )
    synthesiser = make_agent(
        role="Research Synthesiser",
        goal="Produce accurate, cross-verified research answers from reconciled multi-source data.",
        backstory="Senior analyst who integrates diverse data sources into reliable reports.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Search the web for comprehensive information about: {question}. Gather 8+ relevant sources.",
        agent=web_researcher,
        expected_output="Comprehensive web-sourced information with URLs.",
    )
    t2 = make_task(
        description=f"Retrieve relevant financial market data for entities mentioned in: {question}. Look up stock prices, metrics, and financial context.",
        agent=finance_analyst,
        expected_output="Structured financial data including price history, fundamentals, and key metrics.",
    )
    t3 = make_task(
        description=f"Compare the web research and financial data gathered for: {question}. Identify conflicts, note which source is more reliable per data point, and establish a unified fact set.",
        agent=verifier,
        expected_output="A verification report with conflicts identified and a unified fact set.",
    )
    t4 = make_task(
        description=f"Using the verified, reconciled information, write a comprehensive answer to: {question}. Prefer financial data for quantitative claims. Cite sources inline.",
        agent=synthesiser,
        expected_output="A comprehensive, cross-verified research answer.",
    )

    crew = Crew(agents=[web_researcher, finance_analyst, verifier, synthesiser],
                tasks=[t1, t2, t3, t4], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P6", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "token_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P7: Hypothesize → Gather Evidence → Test → Conclude
# ══════════════════════════════════════════════════════════════════════════════

def run_p7(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = _llm()
    scientist = make_agent(
        role="Research Scientist",
        goal="Formulate clear, testable hypotheses for research questions.",
        backstory="Expert at forming precise, falsifiable research claims.",
        tools=[],
        llm=llm,
    )
    supporting_researcher = make_agent(
        role="Supporting Evidence Researcher",
        goal="Find evidence that SUPPORTS the research hypothesis.",
        backstory="Skilled at identifying and evaluating supporting arguments and data.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    refuting_researcher = make_agent(
        role="Counterevidence Researcher",
        goal="Find evidence that CHALLENGES or REFUTES the research hypothesis.",
        backstory="Expert at devil's advocacy and finding counterarguments.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    evaluator = make_agent(
        role="Evidence Evaluator",
        goal="Weigh supporting and refuting evidence objectively to assess the hypothesis.",
        backstory="Critical thinker who evaluates evidence strength and draws balanced conclusions.",
        tools=[],
        llm=llm,
    )
    analyst = make_agent(
        role="Research Analyst",
        goal="Draw clear, well-reasoned conclusions from evidence evaluation.",
        backstory="Senior analyst who translates evidence evaluations into actionable insights.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Form a specific, testable hypothesis (2-3 sentences) addressing: {question}",
        agent=scientist,
        expected_output="A specific, falsifiable research hypothesis.",
    )
    t2 = make_task(
        description=f"Search for evidence SUPPORTING the hypothesis about: {question}. Find 5-6 relevant sources.",
        agent=supporting_researcher,
        expected_output="Supporting evidence with source URLs.",
    )
    t3 = make_task(
        description=f"Search for evidence CHALLENGING or REFUTING the hypothesis about: {question}. Find counterarguments and contradicting data.",
        agent=refuting_researcher,
        expected_output="Refuting evidence and counterarguments with source URLs.",
    )
    t4 = make_task(
        description=f"Evaluate all supporting and refuting evidence. Assess hypothesis strength. Be balanced. Question: {question}",
        agent=evaluator,
        expected_output="A balanced evidence evaluation report.",
    )
    t5 = make_task(
        description=f"Draw final conclusions and write a comprehensive answer to: {question}. Reflect the evidence evaluation honestly.",
        agent=analyst,
        expected_output="A comprehensive, evidence-based final answer.",
    )

    crew = Crew(agents=[scientist, supporting_researcher, refuting_researcher, evaluator, analyst],
                tasks=[t1, t2, t3, t4, t5], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P7", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "token_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P8: Outline → Section-wise Retrieve → Draft → Critique → Revise → Final Edit
# ══════════════════════════════════════════════════════════════════════════════

def run_p8(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = _llm()
    editor = make_agent(
        role="Senior Research Editor",
        goal="Create detailed document outlines that ensure comprehensive, structured research coverage.",
        backstory="20-year veteran editor specialising in research document architecture.",
        tools=[],
        llm=llm,
    )
    researcher = make_agent(
        role="Section Researcher",
        goal="Retrieve targeted information for each section of a research document.",
        backstory="Meticulous researcher skilled at section-specific information gathering.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    writer = make_agent(
        role="Research Writer",
        goal="Draft comprehensive research documents following detailed outlines.",
        backstory="Expert research writer who produces substantive, well-structured documents.",
        tools=[],
        llm=llm,
    )
    peer_reviewer = make_agent(
        role="Peer Reviewer",
        goal="Evaluate research documents for accuracy, completeness, groundedness, and coherence.",
        backstory="Rigorous academic peer reviewer with high standards.",
        tools=[],
        llm=llm,
    )
    reviser = make_agent(
        role="Revision Specialist",
        goal="Improve research documents based on peer review feedback.",
        backstory="Expert at implementing reviewer recommendations to strengthen research output.",
        tools=[],
        llm=llm,
    )
    final_editor = make_agent(
        role="Final Copy Editor",
        goal="Polish research documents to publication quality.",
        backstory="Professional copy editor ensuring flow, style consistency, and executive summaries.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Create a detailed 5-6 section outline for a research document answering: {question}",
        agent=editor,
        expected_output="A numbered 5-6 section outline with brief descriptions of each section's content.",
    )
    t2 = make_task(
        description=f"For each section in the outline, search the web for targeted information. Question: {question}. Label information by section.",
        agent=researcher,
        expected_output="Retrieved information organised by document section.",
    )
    t3 = make_task(
        description=f"Draft the complete research document following the outline structure. Question: {question}. Use ## headers, cite [Source N], be comprehensive.",
        agent=writer,
        expected_output="A complete draft research document with all sections.",
    )
    t4 = make_task(
        description=f"Review the draft research document on: accuracy, completeness, groundedness, coherence, depth. Question: {question}. Give specific numbered feedback.",
        agent=peer_reviewer,
        expected_output="Detailed peer review with numbered recommendations.",
    )
    t5 = make_task(
        description=f"Revise the research document addressing all reviewer feedback. Question: {question}.",
        agent=reviser,
        expected_output="A revised, improved research document.",
    )
    t6 = make_task(
        description=f"Perform final copy-editing on the research document. Add executive summary and key takeaways. Question: {question}.",
        agent=final_editor,
        expected_output="A publication-ready research document with executive summary.",
    )

    crew = Crew(agents=[editor, researcher, writer, peer_reviewer, reviser, final_editor],
                tasks=[t1, t2, t3, t4, t5, t6], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P8", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "token_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P9: Full Research Loop with Adversarial Critique
# ══════════════════════════════════════════════════════════════════════════════

def run_p9(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = _llm()
    planner = make_agent(
        role="Research Strategist",
        goal="Decompose complex research questions into focused sub-questions for comprehensive coverage.",
        backstory="Expert research planner who ensures no aspect of a question is missed.",
        tools=[],
        llm=llm,
    )
    researcher = make_agent(
        role="Multi-Source Researcher",
        goal="Gather comprehensive information from web and financial sources.",
        backstory="Expert at multi-source retrieval and data aggregation.",
        tools=[WEB_TOOL, FINANCE_TOOL],
        llm=llm,
    )
    verifier = make_agent(
        role="Cross-Verification Analyst",
        goal="Identify conflicts across sources and establish a reliable, unified fact set.",
        backstory="Data integrity specialist who reconciles contradictory information.",
        tools=[],
        llm=llm,
    )
    synthesiser = make_agent(
        role="Research Synthesiser",
        goal="Produce comprehensive research answers from verified information.",
        backstory="Senior research analyst skilled at producing structured, evidence-based reports.",
        tools=[],
        llm=llm,
    )
    red_team = make_agent(
        role="Red Team Critic",
        goal="Aggressively identify every weakness, error, and gap in a research draft.",
        backstory="Expert adversarial reviewer tasked with finding every flaw before publication.",
        tools=[],
        llm=llm,
    )
    reviser = make_agent(
        role="Research Reviser",
        goal="Strengthen research answers by addressing adversarial critique comprehensively.",
        backstory="Expert at turning good research into excellent, adversarially robust reports.",
        tools=[],
        llm=llm,
    )
    reporter = make_agent(
        role="Report Formatter",
        goal="Format research into polished, professional reports with executive summaries.",
        backstory="Professional research communications specialist.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Decompose into 4-6 focused sub-questions: {question}",
        agent=planner,
        expected_output="4-6 numbered sub-questions for comprehensive research.",
    )
    t2 = make_task(
        description=f"Search web and financial sources for each sub-question. Question: {question}",
        agent=researcher,
        expected_output="Comprehensive multi-source retrieved information.",
    )
    t3 = make_task(
        description=f"Cross-verify all retrieved information for: {question}. Flag conflicts, establish unified facts.",
        agent=verifier,
        expected_output="A cross-verification report and unified fact set.",
    )
    t4 = make_task(
        description=f"Synthesise verified information into a comprehensive research answer to: {question}",
        agent=synthesiser,
        expected_output="A comprehensive research synthesis with citations.",
    )
    t5 = make_task(
        description=f"ADVERSARIALLY CRITIQUE the synthesis for: {question}. Attack every weakness: errors, gaps, overstatements, missing counterarguments.",
        agent=red_team,
        expected_output="A brutal, specific adversarial critique with numbered issues.",
    )
    t6 = make_task(
        description=f"Revise the synthesis addressing ALL adversarial critique points. Question: {question}.",
        agent=reviser,
        expected_output="A strengthened, adversarially-robust research answer.",
    )
    t7 = make_task(
        description=f"Format as professional research report with Executive Summary and Key Conclusions. Question: {question}.",
        agent=reporter,
        expected_output="A polished professional research report.",
    )

    crew = Crew(agents=[planner, researcher, verifier, synthesiser, red_team, reviser, reporter],
                tasks=[t1, t2, t3, t4, t5, t6, t7], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P9", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "token_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P10: Academic Workflow with Multi-agent Peer Review
# ══════════════════════════════════════════════════════════════════════════════

def run_p10(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = _llm()
    lit_reviewer = make_agent(
        role="Literature Review Specialist",
        goal="Conduct comprehensive literature and web scans on research topics.",
        backstory="PhD-level researcher skilled at systematic literature reviews.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    gap_analyst = make_agent(
        role="Research Gap Analyst",
        goal="Identify gaps and opportunities in existing knowledge on a topic.",
        backstory="Expert at meta-analysis who identifies what is known, unknown, and contested.",
        tools=[],
        llm=llm,
    )
    hypothesis_former = make_agent(
        role="Research Hypothesis Designer",
        goal="Formulate novel, testable research hypotheses that address knowledge gaps.",
        backstory="Academic researcher with expertise in hypothesis formation and research design.",
        tools=[],
        llm=llm,
    )
    methodology_designer = make_agent(
        role="Methodology Expert",
        goal="Design rigorous analytical frameworks for research investigations.",
        backstory="Research methodology specialist ensuring analytical rigour.",
        tools=[],
        llm=llm,
    )
    field_researcher = make_agent(
        role="Field Researcher",
        goal="Gather evidence systematically per the analytical framework.",
        backstory="Skilled at targeted evidence gathering per research designs.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    paper_writer = make_agent(
        role="Academic Paper Author",
        goal="Write comprehensive research papers in proper academic format.",
        backstory="Experienced academic writer skilled at producing journal-quality research papers.",
        tools=[],
        llm=llm,
    )
    methodology_reviewer = make_agent(
        role="Methodology Peer Reviewer",
        goal="Review research papers for methodological rigour and analytical validity.",
        backstory="Expert reviewer focusing exclusively on research design and methodology.",
        tools=[],
        llm=llm,
    )
    clarity_reviewer = make_agent(
        role="Clarity Peer Reviewer",
        goal="Review research papers for writing clarity, structure, and communication quality.",
        backstory="Writing expert who ensures research is clearly and effectively communicated.",
        tools=[],
        llm=llm,
    )
    evidence_reviewer = make_agent(
        role="Evidence Peer Reviewer",
        goal="Review research papers for evidence quality, citation accuracy, and factual correctness.",
        backstory="Fact-checking expert who evaluates the strength and reliability of evidence.",
        tools=[],
        llm=llm,
    )
    reviser = make_agent(
        role="Paper Reviser",
        goal="Revise research papers to address all peer reviewer feedback comprehensively.",
        backstory="Expert at iterative manuscript revision based on peer review.",
        tools=[],
        llm=llm,
    )
    publisher = make_agent(
        role="Journal Editor",
        goal="Perform final copy-editing to produce publication-ready research.",
        backstory="Experienced journal editor ensuring professional, polished academic output.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(description=f"Conduct a literature scan on: {question}", agent=lit_reviewer, expected_output="Comprehensive literature scan results.")
    t2 = make_task(description=f"Identify research gaps from the literature scan on: {question}", agent=gap_analyst, expected_output="Research gaps and opportunities identified.")
    t3 = make_task(description=f"Formulate a novel research hypothesis addressing the gaps for: {question}", agent=hypothesis_former, expected_output="A specific, testable research hypothesis.")
    t4 = make_task(description=f"Design an analytical framework for the hypothesis on: {question}", agent=methodology_designer, expected_output="A detailed analytical framework.")
    t5 = make_task(description=f"Gather evidence per the analytical framework for: {question}", agent=field_researcher, expected_output="Evidence gathered per the framework.")
    t6 = make_task(description=f"Write a full academic research paper (Abstract, Intro, Background, Analysis, Discussion, Conclusion) on: {question}", agent=paper_writer, expected_output="A complete academic research paper.")
    t7 = make_task(description=f"Methodology review of the paper on: {question}. Give numbered recommendations.", agent=methodology_reviewer, expected_output="Methodology peer review with numbered recommendations.")
    t8 = make_task(description=f"Clarity review of the paper on: {question}. Give numbered recommendations.", agent=clarity_reviewer, expected_output="Clarity peer review with numbered recommendations.")
    t9 = make_task(description=f"Evidence review of the paper on: {question}. Give numbered recommendations.", agent=evidence_reviewer, expected_output="Evidence peer review with numbered recommendations.")
    t10 = make_task(description=f"Revise the paper addressing ALL three reviewer recommendations for: {question}", agent=reviser, expected_output="A revised, improved research paper.")
    t11 = make_task(description=f"Final copy-editing for publication. Add structured abstract. Topic: {question}", agent=publisher, expected_output="A publication-ready research paper.")

    all_agents = [lit_reviewer, gap_analyst, hypothesis_former, methodology_designer,
                  field_researcher, paper_writer, methodology_reviewer, clarity_reviewer,
                  evidence_reviewer, reviser, publisher]
    all_tasks = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11]

    crew = Crew(agents=all_agents, tasks=all_tasks, process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P10", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "token_count": len(answer.split()),
            "run_id": run_id, "seed": seed}
