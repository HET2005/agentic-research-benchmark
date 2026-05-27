# run_benchmark.py
import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from questions.question_set import QUESTIONS
from evals.judge import score_answer

RUNS_DIR = ROOT / "runs"
RUNS_DIR.mkdir(exist_ok=True)

ALL_PIPELINES = ["P1","P2","P3","P4","P5","P6","P7","P8","P9","P10"]
ALL_FRAMEWORKS = ["langgraph", "crewai", "autogen"]

def get_runner(framework: str, pipeline: str):
    if framework == "langgraph":
        from frameworks.langgraph import RUNNERS
    elif framework == "crewai":
        from frameworks.crewai import RUNNERS
    elif framework == "autogen":
        from frameworks.autogen import RUNNERS
    else:
        raise ValueError(f"Unknown framework: {framework}")
    return RUNNERS[pipeline]

def run_one(framework, pipeline, question_dict, seed, run_id) -> dict:
    runner = get_runner(framework, pipeline)
    q = question_dict["question"]
    qid = question_dict["id"]
    try:
        t0 = time.perf_counter()
        result = runner(q, run_id=run_id, seed=seed)
        total_latency = time.perf_counter() - t0

        result["question_id"] = qid
        result["category"] = question_dict["category"]
        result["difficulty"] = question_dict["difficulty"]
        result["tier"] = {"P1":"short","P2":"short","P3":"short",
                          "P4":"medium","P5":"medium","P6":"medium","P7":"medium",
                          "P8":"long","P9":"long","P10":"long"}.get(pipeline, "unknown")

        # BUG 6 FIX: Force outer timer as canonical latency to measure the full multi-step pipeline
        result["latency"] = round(total_latency, 3)

        # BUG 1 FIX: Properly extract nested state dicts (Crucial for LangGraph)
        raw_answer = result.get("answer", "")
        if isinstance(raw_answer, dict):
            extracted = raw_answer.get("final_answer") or raw_answer.get("output") or raw_answer.get("content")
            if not extracted and "messages" in raw_answer:
                msg = raw_answer["messages"][-1]
                extracted = msg.content if hasattr(msg, "content") else str(msg)
            answer = str(extracted or raw_answer)
        else:
            answer = str(raw_answer)

        result["answer"] = answer
        result["word_count"] = len(answer.split()) # BUG 9 FIX: Calculate true word count here

        # BUG 4 FIX: Catch embedded errors (not just startswith) to prevent scoring mock/error garbage
        error_prefixes = ("[LLM ERROR]", "[MOCK]", "[CREWAI MOCK", "[CREW ERROR]", "[NO_API_KEY]")
        if not answer.strip() or any(p in answer for p in error_prefixes):
            result["status"] = "error"
            result["error"] = answer[:200] if answer.strip() else "Empty or nested answer returned."
            # Immediately zero out scores to prevent the Judge from hallucinating a valid score
            result.update({
                "accuracy": 0, "completeness": 0, "groundedness": 0,
                "coherence": 0, "overall": 0.0, "reasoning": "Error or empty answer detected."
            })
        else:
            result["status"] = "ok"
            rubric = question_dict.get("rubric", {})
            if rubric:
                scores = score_answer(q, answer, rubric)
                result.update(scores)

    except Exception as e:
        result = {
            "pipeline": pipeline, "framework": framework,
            "question": q, "question_id": qid,
            "answer": "", "latency": 0, "word_count": 0,
            "run_id": run_id, "seed": seed, "status": "error",
            "error": str(e),
        }
    return result

def save_result(result: dict, run_id: str):
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{result['framework']}_{result['pipeline']}_{result.get('question_id','?')}_s{result.get('seed',0)}.json"
    (out_dir / fname).write_text(json.dumps(result, indent=2), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Agentic Pipeline Benchmark Runner")
    parser.add_argument("--frameworks", nargs="+", default=ALL_FRAMEWORKS, choices=ALL_FRAMEWORKS)
    parser.add_argument("--pipelines", nargs="+", default=ALL_PIPELINES, choices=ALL_PIPELINES)
    parser.add_argument("--questions", nargs="+", default=None)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    questions = [q for q in QUESTIONS if (args.questions is None or q["id"] in args.questions)]

    total = len(args.frameworks) * len(args.pipelines) * len(questions) * args.seeds
    print(f"\n{'='*60}\nBenchmark Run: {run_id}\nTotal runs: {total}\n{'='*60}\n")

    done, errors = 0, 0
    all_results = []

    for fw in args.frameworks:
        for pid in args.pipelines:
            for q_dict in questions:
                for seed in range(args.seeds):
                    done += 1
                    print(f"[{done}/{total}] {fw}/{pid}/{q_dict['id']}/s{seed} ...", end=" ", flush=True)
                    t0 = time.perf_counter()
                    result = run_one(fw, pid, q_dict, seed, run_id)
                    elapsed = time.perf_counter() - t0

                    if result["status"] == "ok":
                        print(f"OK  score={result.get('overall', '?')} latency={elapsed:.1f}s")
                    else:
                        errors += 1
                        print(f"ERR {result.get('error','')[:60]}")

                    save_result(result, run_id)
                    all_results.append(result)

    summary_path = RUNS_DIR / run_id / "summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\n{'='*60}\nDone. {done} runs, {errors} errors.\n{'='*60}")

if __name__ == "__main__":
    main()