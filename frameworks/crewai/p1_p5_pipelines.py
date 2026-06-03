"""
frameworks/crewai/p1_retrieve_synthesize.py  — P1 (Short)
frameworks/crewai/p2_query_rewrite.py        — P2 (Short)
frameworks/crewai/p3_decompose_parallel.py   — P3 (Short)
frameworks/crewai/p4_plan_retrieve_draft_cite.py — P4 (Medium)
frameworks/crewai/p5_retrieve_draft_critique_revise.py — P5 (Medium)
"""
import os
import time
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-dummy-not-used")
os.environ["CREWAI_TRACING_ENABLED"] = "false"

from crewai import Crew, Process
from .base import WEB_TOOL, FINANCE_TOOL, make_agent, make_task, run_crew, Timer, get_shared_llm

# ══════════════════════════════════════════════════════════════════════════════
# P1: Retrieve → Synthesize
# ══════════════════════════════════════════════════════════════════════════════

def run_p1(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = get_shared_llm(seed=seed)
    researcher = make_agent(
        role="Research Specialist",
        goal="Retrieve accurate, relevant information from the web to answer research questions.",
        backstory="Expert web researcher skilled at finding and evaluating online sources.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    synthesiser = make_agent(
        role="Research Synthesiser",
        goal="Produce comprehensive, well-structured research answers from gathered information.",
        backstory="Senior analyst who turns raw research into clear, cited, structured reports.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Search the web for comprehensive information to answer: {question}. Gather at least 5-8 relevant sources.",
        agent=researcher,
        expected_output="A collection of relevant information with source URLs.",
    )
    t2 = make_task(
        description=f"Using the retrieved information, write a comprehensive, well-structured answer to: {question}. Cite sources inline as [Source N].",
        agent=synthesiser,
        expected_output="A comprehensive research answer with inline citations.",
    )

    crew = Crew(agents=[researcher, synthesiser], tasks=[t1, t2], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P1", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "word_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P2: Query Rewrite → Retrieve → Answer
# ══════════════════════════════════════════════════════════════════════════════

def run_p2(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = get_shared_llm(seed=seed)
    query_expert = make_agent(
        role="Search Query Optimisation Expert",
        goal="Rewrite research questions into optimal search queries that maximise recall.",
        backstory="Specialist in information retrieval and search engine query optimisation.",
        tools=[],
        llm=llm,
    )
    researcher = make_agent(
        role="Web Researcher",
        goal="Retrieve comprehensive information using optimised search queries.",
        backstory="Skilled at finding and evaluating high-quality web sources.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    writer = make_agent(
        role="Research Writer",
        goal="Write comprehensive, well-cited answers from retrieved information.",
        backstory="Expert research writer who produces clear, structured, evidence-based reports.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Rewrite the following research question as 2-3 optimal search engine queries (max 12 words each) to maximise information recall. Question: {question}",
        agent=query_expert,
        expected_output="2-3 optimised search queries, one per line.",
    )
    t2 = make_task(
        description=f"Use the optimised queries to search the web and gather comprehensive information for answering: {question}",
        agent=researcher,
        expected_output="Comprehensive retrieved information with source URLs.",
    )
    t3 = make_task(
        description=f"Write a comprehensive, well-structured answer to: {question}. Use the retrieved information and cite sources as [Source N].",
        agent=writer,
        expected_output="A comprehensive research answer with inline citations.",
    )

    crew = Crew(agents=[query_expert, researcher, writer], tasks=[t1, t2, t3], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P2", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "word_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P3: Decompose → Parallel Retrieve → Merge
# ══════════════════════════════════════════════════════════════════════════════

def run_p3(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = get_shared_llm(seed=seed)
    planner = make_agent(
        role="Research Planner",
        goal="Break complex research questions into focused, searchable sub-questions.",
        backstory="Expert at decomposing multi-faceted research questions for targeted retrieval.",
        tools=[],
        llm=llm,
    )
    researcher = make_agent(
        role="Multi-Query Researcher",
        goal="Search for each sub-question and gather comprehensive information from multiple angles.",
        backstory="Skilled researcher who can handle multiple parallel research threads.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    synthesiser = make_agent(
        role="Information Synthesiser",
        goal="Merge information from multiple research threads into a single coherent answer.",
        backstory="Senior analyst expert at integrating diverse information into clear, unified reports.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Decompose this research question into 4-5 specific, searchable sub-questions: {question}. List each sub-question numbered.",
        agent=planner,
        expected_output="4-5 numbered sub-questions covering all aspects of the original question.",
    )
    t2 = make_task(
        description=f"For each sub-question provided, search the web and gather relevant information. Original question: {question}. Search each sub-question separately for comprehensive coverage.",
        agent=researcher,
        expected_output="Information gathered for each sub-question, clearly labelled.",
    )
    t3 = make_task(
        description=f"Merge all gathered information into a single comprehensive answer to: {question}. Ensure all aspects are covered and cite sources as [Source N].",
        agent=synthesiser,
        expected_output="A comprehensive, integrated research answer.",
    )

    crew = Crew(agents=[planner, researcher, synthesiser], tasks=[t1, t2, t3], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P3", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "word_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P4: Plan → Retrieve → Draft → Cite-check
# ══════════════════════════════════════════════════════════════════════════════

def run_p4(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = get_shared_llm(seed=seed)
    planner = make_agent(
        role="Senior Research Analyst",
        goal="Create detailed research plans that ensure comprehensive, structured coverage.",
        backstory="20 years experience in research planning for think tanks and consultancies.",
        tools=[],
        llm=llm,
    )
    researcher = make_agent(
        role="Research Specialist",
        goal="Retrieve information guided by a research plan for maximum relevance.",
        backstory="Expert researcher skilled at targeted information retrieval.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    writer = make_agent(
        role="Research Writer",
        goal="Draft comprehensive, structured research documents following research plans.",
        backstory="Expert writer producing high-quality, structured research reports.",
        tools=[],
        llm=llm,
    )
    fact_checker = make_agent(
        role="Fact-Checker and Citation Verifier",
        goal="Ensure every claim in a research document is supported by a valid source citation.",
        backstory="Meticulous editor who verifies factual accuracy and citation completeness.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Create a detailed research plan for: {question}. Include: (1) key topics to cover, (2) specific information to retrieve, (3) suggested answer structure.",
        agent=planner,
        expected_output="A structured research plan with topics, retrieval targets, and answer structure.",
    )
    t2 = make_task(
        description=f"Following the research plan, search the web and retrieve information for all topics identified. Question: {question}",
        agent=researcher,
        expected_output="Comprehensive information organised by research plan sections.",
    )
    t3 = make_task(
        description=f"Using the research plan and retrieved information, draft a comprehensive answer to: {question}. Use section headers and cite sources as [Source N].",
        agent=writer,
        expected_output="A full draft research answer with headers and inline citations.",
    )
    t4 = make_task(
        description=f"Review the draft answer for: {question}. Verify every major claim has a citation. Add missing citations where possible or flag unsupported claims. Produce the final verified answer.",
        agent=fact_checker,
        expected_output="A citation-verified final answer with a brief citation report.",
    )

    crew = Crew(agents=[planner, researcher, writer, fact_checker], tasks=[t1, t2, t3, t4], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P4", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "word_count": len(answer.split()),
            "run_id": run_id, "seed": seed}


# ══════════════════════════════════════════════════════════════════════════════
# P5: Retrieve → Draft → Self-critique → Revise
# ══════════════════════════════════════════════════════════════════════════════

def run_p5(question: str, run_id: str = "default", seed: int = 0) -> dict:
    llm = get_shared_llm(seed=seed)
    researcher = make_agent(
        role="Research Specialist",
        goal="Retrieve comprehensive, accurate information from the web.",
        backstory="Expert web researcher with strong source evaluation skills.",
        tools=[WEB_TOOL],
        llm=llm,
    )
    writer = make_agent(
        role="Research Writer",
        goal="Draft comprehensive research answers from retrieved information.",
        backstory="Skilled research writer who produces structured, well-cited content.",
        tools=[],
        llm=llm,
    )
    critic = make_agent(
        role="Critical Reviewer",
        goal="Identify weaknesses in research answers: errors, gaps, poor citations, incoherence.",
        backstory="Rigorous peer reviewer who evaluates accuracy, completeness, groundedness, and coherence.",
        tools=[],
        llm=llm,
    )
    editor = make_agent(
        role="Research Editor",
        goal="Improve research answers based on critique to produce the best possible final version.",
        backstory="Senior editor who transforms good drafts into excellent final reports.",
        tools=[],
        llm=llm,
    )

    t1 = make_task(
        description=f"Search the web comprehensively for information to answer: {question}. Aim for 8+ relevant sources.",
        agent=researcher,
        expected_output="Comprehensive retrieved information with source URLs.",
    )
    t2 = make_task(
        description=f"Draft a comprehensive answer to: {question}. Use the retrieved information, add section headers, cite sources as [Source N].",
        agent=writer,
        expected_output="A full draft research answer.",
    )
    t3 = make_task(
        description=f"Critique the draft answer on: (1) Accuracy, (2) Completeness, (3) Coherence, (4) Groundedness. Be specific and actionable. Question was: {question}",
        agent=critic,
        expected_output="A detailed critique with specific improvement suggestions per dimension.",
    )
    t4 = make_task(
        description=f"Revise the draft based on the critique to produce the final, improved answer to: {question}. Address every critique point raised.",
        agent=editor,
        expected_output="The improved final research answer.",
    )

    crew = Crew(agents=[researcher, writer, critic, editor], tasks=[t1, t2, t3, t4], process=Process.sequential, verbose=False)
    with Timer() as t:
        answer = run_crew(crew, {"question": question})
    return {"pipeline": "P5", "framework": "crewai", "question": question,
            "answer": answer, "latency": t.elapsed, "word_count": len(answer.split()),
            "run_id": run_id, "seed": seed}

# ── Aliases for clean import ──────────────────────────────────────────────────
run = run_p1