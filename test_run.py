"""
test_run.py — Smoke test: runs P1, P4, P5 across all 3 frameworks on one question.
Run this first to verify everything works before the full benchmark.

Usage:
  cd agentic-bench
  python test_run.py
"""

import sys
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

TEST_QUESTION = "What are the key trends shaping the AI industry in 2024?"

def test_framework(framework_name: str, pipelines=("P1", "P4", "P5")):
    print(f"\n{'='*50}")
    print(f"Testing: {framework_name.upper()}")
    print(f"{'='*50}")

    if framework_name == "langgraph":
        from frameworks.langgraph import RUNNERS
    elif framework_name == "crewai":
        from frameworks.crewai import RUNNERS
    elif framework_name == "autogen":
        from frameworks.autogen import RUNNERS

    for pid in pipelines:
        print(f"\n  [{framework_name}] Running {pid}...", end=" ", flush=True)
        try:
            result = RUNNERS[pid](TEST_QUESTION, run_id="smoke_test", seed=0)
            ans_len = len(result.get("answer", ""))
            latency = result.get("latency", 0)
            print(f"OK | answer={ans_len} chars | latency={latency:.2f}s")
            if ans_len < 10:
                print(f"    WARNING: answer suspiciously short!")
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback; traceback.print_exc()


if __name__ == "__main__":
    for fw in ["langgraph", "crewai", "autogen"]:
        test_framework(fw)
    print("\n\nSmoke test complete.")