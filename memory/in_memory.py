# memory/in_memory.py
"""
Baseline: plain Python list — no external dependency.
Used as the control group; represents a raw LLM with no memory solution.
"""
from collections import defaultdict
from .base_memory import BaseMemory


class InMemory(BaseMemory):
    """Simple in-process list store — the baseline / control."""

    def __init__(self):
        self._store: dict[str, list[dict]] = defaultdict(list)

    @property
    def name(self) -> str:
        return "InMemory (baseline)"

    def add(self, role: str, content: str, session_id: str = "default") -> None:
        self._store[session_id].append({"role": role, "content": content})

    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        """Keyword overlap scoring — no embeddings."""
        turns = self._store.get(session_id, [])
        if not turns:
            return ""
        query_words = set(query.lower().split())
        scored = []
        for i, t in enumerate(turns):
            overlap = len(query_words & set(t["content"].lower().split()))
            scored.append((overlap, i, t))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top = [x[2] for x in scored[:top_k]]
        return "\n".join(f"[{t['role']}]: {t['content']}" for t in top)

    def extract_patterns(self, session_id: str = "default") -> str:
        turns = self._store.get(session_id, [])
        if not turns:
            return "No turns stored."
        # Count word frequency as a naive proxy for patterns
        from collections import Counter
        stop = {"the","a","an","is","are","was","were","in","of","to","and","or","for","on","with","it","this","that","be","have","has","i","we","you"}
        words = []
        for t in turns:
            words += [w.lower().strip(".,?!") for w in t["content"].split() if w.lower() not in stop and len(w) > 3]
        top_words = Counter(words).most_common(10)
        return "Top recurring terms: " + ", ".join(f"{w}({c})" for w, c in top_words)

    def reset(self, session_id: str = "default") -> None:
        self._store[session_id] = []