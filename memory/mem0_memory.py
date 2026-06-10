# memory/mem0_memory.py
import os
import shutil
from .base_memory import BaseMemory

try:
    from mem0 import Memory as Mem0
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

QDRANT_PATH = "./memory/qdrant_store"
EMBED_DIMS = 384  # all-MiniLM-L6-v2


class Mem0Memory(BaseMemory):

    def __init__(self):
        if not MEM0_AVAILABLE:
            raise ImportError("mem0ai not installed. Run: pip install mem0ai")

        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key or groq_key.startswith("sk-dummy"):
            raise RuntimeError("mem0 requires GROQ_API_KEY in .env")

        # Wipe stale qdrant store if it exists (could have wrong embedding dims from previous run)
        if os.path.exists(QDRANT_PATH):
            shutil.rmtree(QDRANT_PATH, ignore_errors=True)

        config = {
            "llm": {
                "provider": "groq",
                "config": {
                    "model": "llama-3.1-8b-instant",
                    "api_key": groq_key,
                    "temperature": 0.1,
                    "max_tokens": 1000,
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "all-MiniLM-L6-v2",
                    "embedding_dims": EMBED_DIMS,
                }
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "bench_memory",
                    "path": QDRANT_PATH,
                    "embedding_model_dims": EMBED_DIMS,
                }
            },
            "version": "v1.1"
        }

        try:
            self._mem = Mem0.from_config(config)
        except Exception as e:
            raise RuntimeError(f"mem0 init failed: {e}")

    @property
    def name(self) -> str:
        return "mem0"

    def _clean(self, session_id: str) -> str:
        return "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))

    def add(self, role: str, content: str, session_id: str = "default") -> None:
        try:
            self._mem.add(
                messages=[{"role": role, "content": content}],
                user_id=self._clean(session_id)
            )
        except Exception as e:
            print(f"    [mem0 add warning: {e}]")

    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        sid = self._clean(session_id)
        try:
            results = self._mem.search(
                query=query,
                filters={"user_id": sid},
                limit=top_k
            )
            if not results:
                return ""
            items = results.get("results", results) if isinstance(results, dict) else results
            if not items:
                return ""
            return "\n".join(
                r.get("memory", str(r)) for r in items if isinstance(r, dict)
            )
        except Exception as e:
            return f"[mem0 recall error: {e}]"

    def extract_patterns(self, session_id: str = "default") -> str:
        sid = self._clean(session_id)
        try:
            all_mem = self._mem.get_all(filters={"user_id": sid})
            items = all_mem.get("results", all_mem) if isinstance(all_mem, dict) else all_mem
            if not items:
                return "No memories stored."
            return "\n".join(
                f"- {m.get('memory', str(m))}" for m in items[:10] if isinstance(m, dict)
            )
        except Exception as e:
            return f"[mem0 pattern error: {e}]"

    def reset(self, session_id: str = "default") -> None:
        try:
            self._mem.delete_all(user_id=self._clean(session_id))
        except Exception:
            pass