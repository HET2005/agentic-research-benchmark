# memory/langchain_memory.py
import os
import sys
from pathlib import Path
from collections import defaultdict
from .base_memory import BaseMemory

sys.path.insert(0, str(Path(__file__).parents[1]))

LANGCHAIN_AVAILABLE = False
ConversationSummaryBufferMemory = None

try:
    try:
        from langchain.memory import ConversationSummaryBufferMemory
    except ImportError:
        from langchain_classic.memory import ConversationSummaryBufferMemory
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    pass


def _get_langchain_llm():
    groq_key = os.environ.get("GROQ_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    from langchain_openai import ChatOpenAI
    class PatchedChatOpenAI(ChatOpenAI):
        def get_num_tokens_from_messages(self, messages) -> int:
            return sum(len(getattr(m, "content", "")) // 4 + 4 for m in messages)
        def get_num_tokens(self, text: str) -> int:
            return len(text) // 4

    if groq_key and not groq_key.startswith("sk-dummy"):
        return PatchedChatOpenAI(
            model="llama-3.1-8b-instant",
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.3,
        )
    elif openai_key and not openai_key.startswith("sk-dummy"):
        return PatchedChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=0.3)

    raise RuntimeError("LangChain memory needs GROQ_API_KEY or OPENAI_API_KEY in .env")


class LangChainMemory(BaseMemory):

    def __init__(self, max_token_limit: int = 1000):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain not installed. Run: pip install langchain langchain-community")

        llm = _get_langchain_llm()
        self._memories = {}
        self._llm = llm
        self._max_token_limit = max_token_limit
        self._raw = defaultdict(list)
        self._pending = ""

    @property
    def name(self) -> str:
        return "LangChain SummaryBuffer"

    def _get_mem(self, session_id: str):
        if session_id not in self._memories:
            self._memories[session_id] = ConversationSummaryBufferMemory(
                llm=self._llm,
                max_token_limit=self._max_token_limit,
                return_messages=True,
            )
        return self._memories[session_id]

    def add(self, role: str, content: str, session_id: str = "default") -> None:
        mem = self._get_mem(session_id)
        self._raw[session_id].append({"role": role, "content": content})
        if role in ("user", "human"):
            self._pending = content
        else:
            human = self._pending
            if human:
                mem.save_context({"input": human}, {"output": content})
                self._pending = ""

    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        mem = self._get_mem(session_id)
        try:
            history = mem.load_memory_variables({})
            messages = history.get("history", [])
            if isinstance(messages, list):
                recent = messages[-top_k * 2:]
                return "\n".join(f"[{m.type}]: {m.content}" for m in recent)
            return str(messages)
        except Exception as e:
            return f"[LangChain recall error: {e}]"

    def extract_patterns(self, session_id: str = "default") -> str:
        mem = self._get_mem(session_id)
        try:
            summary = mem.moving_summary_buffer
            if summary:
                return f"Running summary:\n{summary}"
            from collections import Counter
            stop = {"the","a","an","is","are","was","in","of","to","and","or","for","on","with","it"}
            words = []
            for t in self._raw.get(session_id, []):
                words += [w.lower().strip(".,?!") for w in t["content"].split()
                          if w.lower() not in stop and len(w) > 3]
            top = Counter(words).most_common(8)
            return "Top terms: " + ", ".join(f"{w}({c})" for w, c in top)
        except Exception as e:
            return f"[LangChain pattern error: {e}]"

    def reset(self, session_id: str = "default") -> None:
        if session_id in self._memories:
            self._memories[session_id].clear()
            del self._memories[session_id]
        self._raw[session_id] = []