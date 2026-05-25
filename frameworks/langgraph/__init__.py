from .p1_retrieve_synthesize import run as p1_run
from .p2_query_rewrite import run as p2_run
from .p3_decompose_parallel import run as p3_run
from .p4_plan_retrieve_draft_cite import run as p4_run
from .p5_retrieve_draft_critique_revise import run as p5_run
from .p6_multisource_crossverify import run as p6_run
from .p7_hypothesize_test_conclude import run as p7_run
from .p8_outline_sectionwise_full import run as p8_run
from .p9_full_research_adversarial import run as p9_run
from .p10_academic_workflow import run as p10_run

RUNNERS = {
    "P1": p1_run, "P2": p2_run, "P3": p3_run, "P4": p4_run, "P5": p5_run,
    "P6": p6_run, "P7": p7_run, "P8": p8_run, "P9": p9_run, "P10": p10_run,
}