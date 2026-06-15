# memory/zep_memory.py
import os
import uuid
from .base_memory import BaseMemory

try:
    from zep_cloud.client import Zep
    ZEP_AVAILABLE = True
except ImportError:
    ZEP_AVAILABLE = False


class ZepMemory(BaseMemory):

    def __init__(self):
        if not ZEP_AVAILABLE:
            raise ImportError("Run: pip install zep-cloud")

        api_key = os.environ.get("ZEP_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ZEP_API_KEY not set in .env")

        try:
            self._client = Zep(api_key=api_key)
            try:
                self._client.user.add(user_id="bench_user", first_name="Bench")
            except Exception:
                pass
        except Exception as e:
            raise RuntimeError(f"Zep init failed: {e}")

        self._threads: dict[str, str] = {}

    @property
    def name(self) -> str:
        return "Zep"

    def _get_thread(self, session_id: str) -> str:
        if session_id not in self._threads:
            thread_id = f"bench-{uuid.uuid4().hex[:12]}"
            try:
                self._client.thread.create(
                    thread_id=thread_id,
                    user_id="bench_user"
                )
            except Exception as e:
                raise RuntimeError(f"Zep create thread failed: {e}")
            self._threads[session_id] = thread_id
        return self._threads[session_id]

    def add(self, role: str, content: str, session_id: str = "default") -> None:
        try:
            thread_id = self._get_thread(session_id)
            zep_role = "user" if role in ("user", "human") else "assistant"
            self._client.thread.add_messages(
                thread_id=thread_id,
                messages=[{"role": zep_role, "content": content}]
            )
        except Exception as e:
            print(f"    [Zep add warning: {e}]")

    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        try:
            thread_id = self._get_thread(session_id)
            result = self._client.thread.get(thread_id=thread_id)
            if result and hasattr(result, "context") and result.context:
                return result.context[:600]
            if result and hasattr(result, "messages") and result.messages:
                return "\n".join(
                    f"[{m.role}]: {m.content}"
                    for m in result.messages[-top_k:]
                )
        except Exception as e:
            return f"[Zep recall error: {e}]"
        return ""
    def extract_patterns(self, session_id: str = "default") -> str:
        try:
            thread_id = self._threads.get(session_id)
            if not thread_id:
                return "No thread created yet."
        # get_user_context gives facts/summary at user level
            result = self._client.thread.get_user_context(thread_id=thread_id)
            parts = []
            if result and hasattr(result, "context") and result.context:
                parts.append(f"Context: {result.context[:400]}")
            if result and hasattr(result, "facts") and result.facts:
                parts.append("Facts:\n" + "\n".join(f"- {f}" for f in result.facts[:6]))
            return "\n".join(parts) if parts else "No patterns extracted yet."
        except Exception as e:
            return f"[Zep pattern error: {e}]"
   

    def reset(self, session_id: str = "default") -> None:
        thread_id = self._threads.get(session_id)
        if thread_id:
            try:
                self._client.thread.delete(thread_id=thread_id)
            except Exception:
                pass
            del self._threads[session_id]