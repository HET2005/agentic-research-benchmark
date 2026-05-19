from .langgraph import RUNNERS as LG_RUNNERS
from .crewai import RUNNERS as CR_RUNNERS
from .autogen import RUNNERS as AG_RUNNERS

ALL_RUNNERS = {
    "langgraph": LG_RUNNERS,
    "crewai": CR_RUNNERS,
    "autogen": AG_RUNNERS,
}

__all__ = ["ALL_RUNNERS", "LG_RUNNERS", "CR_RUNNERS", "AG_RUNNERS"]