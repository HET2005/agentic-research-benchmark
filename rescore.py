"""
rescore.py — Rescore an existing benchmark run.
Usage: python rescore.py --run-id run_20260525_144626
       python rescore.py  (uses latest run)
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from evals.judge import score_answer, is_error_answer
from questions.question_set import QUESTIONS

parser = argparse.ArgumentParser()
parser.add_argument("--run-id", default=None)
args = parser.parse_args()

runs_dir = Path("runs")
if args.run_id:
    run_path = runs_dir / args.run_id
else:
    dirs = sorted(runs_dir.glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dirs:
        print("No runs found.")
        sys.exit(1)
    run_path = dirs[0]
    print(f"Using latest run: {run_path.name}")

q_map = {q["id"]: q for q in QUESTIONS}
count = 0

for f in sorted(run_path.glob("*.json")):
    if f.name == "summary.json":
        continue
    data = json.loads(f.read_text(encoding="utf-8"))
    qid = data.get("question_id", "")
    q_data = q_map.get(qid, {})
    answer = data.get("answer", "")

    if not q_data or not answer:
        continue

    if is_error_answer(answer):
        data["status"] = "error"
        data["overall"] = 0.0
        data["reasoning"] = "Error or mock answer — not scored."
    else:
        scores = score_answer(data["question"], answer, q_data.get("rubric", {}))
        data.update(scores)
        data["status"] = "ok"

    f.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{data['framework']}/{data['pipeline']}/{qid} "
          f"score={data.get('overall', 0):.2f} words={data.get('word_count', 0)}")
    count += 1

print(f"\nRescoring done. {count} files updated.")