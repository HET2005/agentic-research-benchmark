# memory/in_memory.py
from collections import defaultdict
from .base_memory import BaseMemory


class InMemory(BaseMemory):
    """Baseline: plain keyword-overlap store. No external dependencies."""

    def __init__(self):
        self._store = defaultdict(list)

    @property
    def name(self) -> str:
        return "InMemory (baseline)"

    def add(self, role: str, content: str, session_id: str = "default") -> None:
        self._store[session_id].append({"role": role, "content": content})

    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        turns = self._store.get(session_id, [])
        if not turns:
            return ""
        query_words = set(w.lower().strip(".,?!") for w in query.split() if len(w) > 3)
        scored = []
        for t in turns:
            content_words = set(w.lower().strip(".,?!") for w in t["content"].split())
            overlap = len(query_words & content_words)
            scored.append((overlap, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]
        # If no keyword overlap, fall back to most recent turns
        if not any(score > 0 for score, _ in top):
            recent = turns[-top_k:]
            return "\n".join(f"[{t['role']}]: {t['content']}" for t in recent)
        return "\n".join(f"[{t['role']}]: {t['content']}" for _, t in top)

    def extract_patterns(self, session_id: str = "default") -> str:
        turns = self._store.get(session_id, [])
        if not turns:
            return "No turns stored."
        from collections import Counter
        stop = {"the","a","an","is","are","was","were","in","of","to","and","or",
                "for","on","with","it","this","that","be","have","has","i","we",
                "you","but","not","they","from","by","as","at","its","also"}
        words = []
        for t in turns:
            words += [w.lower().strip(".,?!") for w in t["content"].split()
                      if w.lower().strip(".,?!") not in stop and len(w) > 3]
        top = Counter(words).most_common(10)
        return "Top recurring terms: " + ", ".join(f"{w}({c})" for w, c in top)

    def reset(self, session_id: str = "default") -> None:
        self._store[session_id] = []