from .pipelines import (
    run_p1, run_p2, run_p3, run_p4, run_p5,
    run_p6, run_p7, run_p8, run_p9, run_p10
)

RUNNERS = {
    "P1": run_p1, "P2": run_p2, "P3": run_p3, "P4": run_p4, "P5": run_p5,
    "P6": run_p6, "P7": run_p7, "P8": run_p8, "P9": run_p9, "P10": run_p10,
}

__all__ = ["RUNNERS"]