"""
run_benchmark.py — Main benchmark runner.
Loops through questions × pipelines × frameworks × seeds.

Usage:
  python run_benchmark.py --frameworks langgraph --pipelines P1 P2 --questions Q01 Q02 --seeds 1
  python run_benchmark.py  # runs all (slow)
"""

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
        result = runner(q, run_id=run_id, seed=seed)
        result["question_id"] = qid
        result["category"] = question_dict["category"]
        result["difficulty"] = question_dict["difficulty"]
        result["tier"] = {"P1":"short","P2":"short","P3":"short",
                          "P4":"medium","P5":"medium","P6":"medium","P7":"medium",
                          "P8":"long","P9":"long","P10":"long"}.get(pipeline, "unknown")

        # Score it
        rubric = question_dict.get("rubric", {})
        if rubric:
            scores = score_answer(q, result.get("answer",""), rubric)
            result.update(scores)
        result["status"] = "ok"
    except Exception as e:
        result = {
            "pipeline": pipeline, "framework": framework,
            "question": q, "question_id": qid,
            "answer": "", "latency": 0, "token_count": 0,
            "run_id": run_id, "seed": seed, "status": "error",
            "error": str(e), "traceback": traceback.format_exc()[-500:],
        }
    return result


def save_result(result: dict, run_id: str):
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{result['framework']}_{result['pipeline']}_{result.get('question_id','?')}_s{result.get('seed',0)}.json"
    (out_dir / fname).write_text(json.dumps(result, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Agentic Pipeline Benchmark Runner")
    parser.add_argument("--frameworks", nargs="+", default=ALL_FRAMEWORKS,
                        choices=ALL_FRAMEWORKS, help="Frameworks to test")
    parser.add_argument("--pipelines", nargs="+", default=ALL_PIPELINES,
                        choices=ALL_PIPELINES, help="Pipelines to test")
    parser.add_argument("--questions", nargs="+", default=None,
                        help="Question IDs to test e.g. Q01 Q02 (default: all)")
    parser.add_argument("--seeds", type=int, default=1,
                        help="Number of seeds (default 1, full run = 10)")
    parser.add_argument("--run-id", default=None,
                        help="Run ID (default: timestamp)")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    questions = [q for q in QUESTIONS if (args.questions is None or q["id"] in args.questions)]

    total = len(args.frameworks) * len(args.pipelines) * len(questions) * args.seeds
    print(f"\n{'='*60}")
    print(f"Benchmark Run: {run_id}")
    print(f"Frameworks: {args.frameworks}")
    print(f"Pipelines:  {args.pipelines}")
    print(f"Questions:  {len(questions)}")
    print(f"Seeds:      {args.seeds}")
    print(f"Total runs: {total}")
    print(f"{'='*60}\n")

    done = 0
    errors = 0
    all_results = []

    for fw in args.frameworks:
        for pid in args.pipelines:
            for q_dict in questions:
                for seed in range(args.seeds):
                    done += 1
                    label = f"[{done}/{total}] {fw}/{pid}/{q_dict['id']}/s{seed}"
                    print(f"{label} ...", end=" ", flush=True)
                    t0 = time.perf_counter()
                    result = run_one(fw, pid, q_dict, seed, run_id)
                    elapsed = time.perf_counter() - t0

                    if result["status"] == "ok":
                        score = result.get("overall", "?")
                        print(f"OK  score={score} latency={elapsed:.1f}s")
                    else:
                        errors += 1
                        print(f"ERR {result.get('error','')[:60]}")

                    save_result(result, run_id)
                    all_results.append(result)

    # Save aggregated results
    summary_path = RUNS_DIR / run_id / "summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"Done. {done} runs, {errors} errors.")
    print(f"Results saved to: {RUNS_DIR / run_id}")
    print(f"{'='*60}")

    return all_results


if __name__ == "__main__":
    main()