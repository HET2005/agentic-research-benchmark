# Agentic Pipeline Benchmark

Compare 10 pipeline designs × 3 frameworks on research tasks.

## Setup

```bash
cd agentic-bench
pip install langgraph crewai yfinance duckduckgo-search anthropic matplotlib pandas
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

## Run smoke test first
```bash
python test_run.py
```

## Run benchmark
```bash
# Quick test (2 questions, P1 only, langgraph, 1 seed)
python run_benchmark.py --frameworks langgraph --pipelines P1 --questions Q01 Q02 --seeds 1

# Medium run
python run_benchmark.py --frameworks langgraph crewai --pipelines P1 P3 P5 --seeds 3

# Full run (slow — 10 seeds, all combos)
python run_benchmark.py --seeds 10
```

## Analyze results
```bash
python results/analyze.py                     # picks latest run
python results/analyze.py --run-id run_XYZ    # specific run
```

## Frameworks
| Framework | Pattern | Strength |
|---|---|---|
| LangGraph | Graph-based stateful | Long pipelines P8-P10 |
| CrewAI | Role-based multi-agent | Medium pipelines P4-P7 |
| AutoGen | Conversational multi-agent | Iterative dialogue P9-P10 |

## Pipelines
| ID | Name | Tier |
|---|---|---|
| P1 | Retrieve → Synthesize | Short |
| P2 | Query Rewrite → Retrieve → Answer | Short |
| P3 | Decompose → Parallel Retrieve → Merge | Short |
| P4 | Plan → Retrieve → Draft → Cite-check | Medium |
| P5 | Retrieve → Draft → Self-critique → Revise | Medium |
| P6 | Multi-source → Cross-verify → Synthesize | Medium |
| P7 | Hypothesize → Evidence → Test → Conclude | Medium |
| P8 | Outline → Section Retrieve → Draft → Critique → Revise → Final | Long |
| P9 | Full Loop + Adversarial Critique | Long |
| P10 | Academic Workflow + Multi-agent Peer Review | Long |

## Project Structure
```
agentic-bench/
├── frameworks/langgraph/   # P1–P10 LangGraph implementations
├── frameworks/crewai/      # P1–P10 CrewAI implementations
├── frameworks/autogen/     # P1–P10 AutoGen implementations
├── tools/                  # yf_tool.py, ddg_tool.py
├── pipelines/              # Framework-agnostic specs
├── questions/              # 25 benchmark questions + rubrics
├── evals/                  # LLM-as-judge scorer
├── runs/                   # Raw outputs per run
├── results/                # CSV + plots
├── run_benchmark.py        # Main runner
├── test_run.py             # Smoke test
└── README.md
```