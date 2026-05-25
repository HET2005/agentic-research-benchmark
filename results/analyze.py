"""
results/analyze.py
Aggregate benchmark results → CSV and Pareto plots.

Usage:
  python results/analyze.py --run-id run_20240101_120000
  python results/analyze.py  # picks latest run
"""

import json
import sys
import argparse
from pathlib import Path

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
    # Fallback: load individual files
    results = []
    for f in run_dir.glob("*.json"):
        try:
            results.append(json.loads(f.read_text()))
        except Exception:
            pass
    return results


def to_csv(results: list, out_path: Path):
    import csv
    fields = ["framework","pipeline","question_id","category","difficulty","tier",
              "seed","latency","token_count","accuracy","completeness",
              "groundedness","coherence","overall","status"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"CSV saved: {out_path}")


def print_summary_table(results: list):
    from collections import defaultdict
    # Group by framework + pipeline
    groups = defaultdict(list)
    for r in results:
        if r.get("status") == "ok":
            key = (r.get("framework","?"), r.get("pipeline","?"))
            groups[key].append(r)

    print(f"\n{'Framework':<12} {'Pipeline':<6} {'N':>4} {'Overall':>8} {'Latency':>9} {'Tokens':>8}")
    print("-" * 55)
    for (fw, pid) in sorted(groups):
        recs = groups[(fw, pid)]
        n = len(recs)
        avg_score = sum(r.get("overall", 0) for r in recs) / n if n else 0
        avg_lat = sum(r.get("latency", 0) for r in recs) / n if n else 0
        avg_tok = sum(r.get("token_count", 0) for r in recs) / n if n else 0
        print(f"{fw:<12} {pid:<6} {n:>4} {avg_score:>8.2f} {avg_lat:>8.1f}s {avg_tok:>8.0f}")


def plot_pareto(results: list, out_path: Path):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        import numpy as np
    except ImportError:
        print("matplotlib not installed — skipping plots.")
        return

    from collections import defaultdict
    groups = defaultdict(list)
    for r in results:
        if r.get("status") == "ok" and r.get("overall") is not None:
            key = (r.get("framework","?"), r.get("pipeline","?"))
            groups[key].append(r)

    frameworks = list({fw for fw, _ in groups})
    colors = {fw: cm.tab10(i/len(frameworks)) for i, fw in enumerate(frameworks)}
    markers = {"langgraph": "o", "crewai": "s", "autogen": "^"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Quality vs Latency (Pareto)
    ax = axes[0]
    for (fw, pid), recs in groups.items():
        avg_score = sum(r.get("overall", 0) for r in recs) / len(recs)
        avg_lat = sum(r.get("latency", 0) for r in recs) / len(recs)
        ax.scatter(avg_lat, avg_score, color=colors[fw],
                   marker=markers.get(fw, "o"), s=100, zorder=5)
        ax.annotate(pid, (avg_lat, avg_score), textcoords="offset points",
                    xytext=(5, 5), fontsize=7)

    # Legend
    for fw in frameworks:
        ax.scatter([], [], color=colors[fw], marker=markers.get(fw,"o"),
                   label=fw, s=80)
    ax.legend(fontsize=9)
    ax.set_xlabel("Avg Latency (s)")
    ax.set_ylabel("Avg Quality Score (0-10)")
    ax.set_title("Quality vs Latency (Pareto)")
    ax.grid(True, alpha=0.3)

    # Plot 2: Quality by pipeline tier
    tiers = {"P1":"short","P2":"short","P3":"short",
             "P4":"medium","P5":"medium","P6":"medium","P7":"medium",
             "P8":"long","P9":"long","P10":"long"}
    tier_colors = {"short": "#2196F3", "medium": "#FF9800", "long": "#4CAF50"}

    ax2 = axes[1]
    pipeline_ids = [f"P{i}" for i in range(1, 11)]
    for fw in frameworks:
        scores_per_pipeline = []
        for pid in pipeline_ids:
            recs = groups.get((fw, pid), [])
            if recs:
                scores_per_pipeline.append(sum(r.get("overall",0) for r in recs)/len(recs))
            else:
                scores_per_pipeline.append(0)
        ax2.plot(pipeline_ids, scores_per_pipeline, marker=markers.get(fw,"o"),
                 label=fw, color=colors[fw])

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
        # Pick latest run
        dirs = sorted(RUNS_DIR.glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not dirs:
            print("No runs found in runs/ directory.")
            return
        run_id = dirs[0].name
        print(f"Using latest run: {run_id}")

    results = load_results(run_id)
    print(f"Loaded {len(results)} results from {run_id}")

    to_csv(results, RESULTS_DIR / f"{run_id}.csv")
    print_summary_table(results)
    plot_pareto(results, RESULTS_DIR / f"{run_id}_pareto.png")


if __name__ == "__main__":
    main()