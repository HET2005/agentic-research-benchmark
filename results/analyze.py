"""
results/analyze.py
"""
import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

RUNS_DIR = ROOT / "runs"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_results(run_id: str) -> list:
    run_dir = RUNS_DIR / run_id
    summary = run_dir / "summary.json"
    if summary.exists():
        return json.loads(summary.read_text())
    results = []
    for f in run_dir.glob("*.json"):
        if f.name == "summary.json":
            continue
        try:
            results.append(json.loads(f.read_text()))
        except Exception:
            pass
    return results


def to_csv(results: list, out_path: Path):
    import csv
    fields = ["framework", "pipeline", "question_id", "category", "difficulty",
              "tier", "seed", "latency", "word_count", "accuracy", "completeness",
              "groundedness", "coherence", "overall", "status"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"CSV saved: {out_path}")


def print_summary_table(results: list):
    groups = defaultdict(list)
    error_groups = defaultdict(int)

    for r in results:
        key = (r.get("framework", "?"), r.get("pipeline", "?"))
        if r.get("status") == "ok" and r.get("overall", 0) > 0:
            groups[key].append(r)
        else:
            error_groups[key] += 1

    print(f"\n{'Framework':<12} {'Pipeline':<8} {'N':>4} {'Overall':>8} "
          f"{'Latency':>9} {'Words':>7} {'Errors':>7} {'ErrRate':>8}")
    print("-" * 70)

    for (fw, pid) in sorted(groups.keys()):
        recs = groups[(fw, pid)]
        n = len(recs)
        errs = error_groups.get((fw, pid), 0)
        total = n + errs
        avg_score = sum(r.get("overall", 0) for r in recs) / n if n else 0
        avg_lat = sum(r.get("latency", 0) for r in recs) / n if n else 0
        avg_words = sum(r.get("word_count", 0) for r in recs) / n if n else 0
        err_rate = errs / total if total else 0
        print(f"{fw:<12} {pid:<8} {n:>4} {avg_score:>8.2f} "
              f"{avg_lat:>8.1f}s {avg_words:>7.0f} {errs:>7} {err_rate:>7.1%}")


def print_question_table(results: list):
    """Per-question breakdown."""
    groups = defaultdict(list)
    for r in results:
        if r.get("status") == "ok" and r.get("overall", 0) > 0:
            key = (r.get("framework", "?"), r.get("question_id", "?"))
            groups[key].append(r.get("overall", 0))

    print(f"\n--- Per-Question Scores ---")
    print(f"{'Framework':<12} {'Question':<10} {'Avg Score':>10} {'N':>4}")
    print("-" * 40)
    for (fw, qid) in sorted(groups.keys()):
        scores = groups[(fw, qid)]
        avg = sum(scores) / len(scores)
        print(f"{fw:<12} {qid:<10} {avg:>10.2f} {len(scores):>4}")


def plot_pareto(results: list, out_path: Path):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
    except ImportError:
        print("matplotlib not installed — skipping plots.")
        return

    groups = defaultdict(list)
    for r in results:
        if r.get("status") == "ok" and r.get("overall", 0) > 0:
            key = (r.get("framework", "?"), r.get("pipeline", "?"))
            groups[key].append(r)

    frameworks = list({fw for fw, _ in groups})
    colors = {fw: cm.tab10(i / max(len(frameworks), 1))
              for i, fw in enumerate(frameworks)}
    markers = {"langgraph": "o", "crewai": "s", "autogen": "^",
               "prompt_chain": "D"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Quality vs Latency
    ax = axes[0]
    for (fw, pid), recs in groups.items():
        avg_score = sum(r.get("overall", 0) for r in recs) / len(recs)
        avg_lat = sum(r.get("latency", 0) for r in recs) / len(recs)
        ax.scatter(avg_lat, avg_score, color=colors[fw],
                   marker=markers.get(fw, "o"), s=100, zorder=5)
        ax.annotate(pid, (avg_lat, avg_score), textcoords="offset points",
                    xytext=(5, 5), fontsize=7)
    for fw in frameworks:
        ax.scatter([], [], color=colors[fw], marker=markers.get(fw, "o"),
                   label=fw, s=80)
    ax.legend(fontsize=9)
    ax.set_xlabel("Avg Latency (s)")
    ax.set_ylabel("Avg Quality Score (0-10)")
    ax.set_title("Quality vs Latency (Pareto)")
    ax.grid(True, alpha=0.3)

    # Plot 2: Quality by pipeline
    pipeline_ids = [f"P{i}" for i in range(1, 11)]
    ax2 = axes[1]
    for fw in frameworks:
        scores_per_pipeline = []
        for pid in pipeline_ids:
            recs = groups.get((fw, pid), [])
            if recs:
                scores_per_pipeline.append(
                    sum(r.get("overall", 0) for r in recs) / len(recs))
            else:
                scores_per_pipeline.append(0)
        ax2.plot(pipeline_ids, scores_per_pipeline,
                 marker=markers.get(fw, "o"), label=fw, color=colors[fw])
    ax2.set_xlabel("Pipeline")
    ax2.set_ylabel("Avg Quality Score (0-10)")
    ax2.set_title("Quality by Pipeline per Framework")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    if args.run_id:
        run_id = args.run_id
    else:
        dirs = sorted(RUNS_DIR.glob("run_*"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        if not dirs:
            print("No runs found.")
            return
        run_id = dirs[0].name
        print(f"Using latest run: {run_id}")

    results = load_results(run_id)
    print(f"Loaded {len(results)} results from {run_id}")

    to_csv(results, RESULTS_DIR / f"{run_id}.csv")
    print_summary_table(results)
    print_question_table(results)
    plot_pareto(results, RESULTS_DIR / f"{run_id}_pareto.png")


if __name__ == "__main__":
    main()