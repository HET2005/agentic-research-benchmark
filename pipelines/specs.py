PIPELINE_SPECS = {
    "P1": {"name": "Retrieve → Synthesize", "tier": "short", "steps": ["retrieve","synthesize"]},
    "P2": {"name": "Query Rewrite → Retrieve → Answer", "tier": "short", "steps": ["rewrite","retrieve","answer"]},
    "P3": {"name": "Decompose → Parallel Retrieve → Merge", "tier": "short", "steps": ["decompose","parallel_retrieve","merge"]},
    "P4": {"name": "Plan → Retrieve → Draft → Cite-check", "tier": "medium", "steps": ["plan","retrieve","draft","cite_check"]},
    "P5": {"name": "Retrieve → Draft → Self-critique → Revise", "tier": "medium", "steps": ["retrieve","draft","self_critique","revise"]},
    "P6": {"name": "Multi-source Retrieve → Cross-verify → Synthesize", "tier": "medium", "steps": ["web_retrieve","finance_retrieve","cross_verify","synthesize"]},
    "P7": {"name": "Hypothesize → Gather Evidence → Test → Conclude", "tier": "medium", "steps": ["hypothesize","gather_supporting","gather_refuting","test","conclude"]},
    "P8": {"name": "Outline → Section Retrieve → Draft → Critique → Revise → Final", "tier": "long", "steps": ["outline","section_retrieve","draft","critique","revise","final_edit"]},
    "P9": {"name": "Full Research Loop with Adversarial Critique", "tier": "long", "steps": ["decompose","multi_retrieve","cross_verify","synthesize","adversarial_critique","revise","report"]},
    "P10": {"name": "Academic Workflow with Multi-agent Peer Review", "tier": "long", "steps": ["lit_scan","identify_gaps","hypothesize","design","execute","peer_review_x3","revise","publish"]},
}

def get_spec(pid: str) -> dict:
    if pid not in PIPELINE_SPECS:
        raise KeyError(f"Pipeline {pid!r} not found.")
    return PIPELINE_SPECS[pid]

def get_by_tier(tier: str) -> dict:
    return {k: v for k, v in PIPELINE_SPECS.items() if v["tier"] == tier}