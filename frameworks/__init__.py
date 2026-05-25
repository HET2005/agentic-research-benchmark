# frameworks/__init__.py
# Lazy imports — don't import at package level to avoid circular/missing module errors

def get_runners(framework: str) -> dict:
    if framework == "langgraph":
        from frameworks.langgraph import RUNNERS
        return RUNNERS
    elif framework == "crewai":
        from frameworks.crewai import RUNNERS
        return RUNNERS
    elif framework == "autogen":
        from frameworks.autogen import RUNNERS
        return RUNNERS
    else:
        raise ValueError(f"Unknown framework: {framework}")

ALL_FRAMEWORKS = ["langgraph", "crewai", "autogen"]