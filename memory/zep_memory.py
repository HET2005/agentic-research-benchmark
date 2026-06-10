# memory/zep_memory.py
import os
import uuid
from .base_memory import BaseMemory

try:
    from zep_cloud.client import Zep
    from zep_cloud.types import Message
    ZEP_AVAILABLE = True
except ImportError:
    ZEP_AVAILABLE = False


class ZepMemory(BaseMemory):

    def __init__(self):
        if not ZEP_AVAILABLE:
            raise ImportError("Run: pip uninstall zep-python && pip install zep-cloud")

        api_key = os.environ.get("ZEP_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ZEP_API_KEY not set in .env")

        try:
            self._client = Zep(api_key=api_key)
            # Create bench user — 409 if already exists is fine
            try:
                self._client.user.add(user_id="bench_user", first_name="Bench")
            except Exception:
                pass
        except Exception as e:
            raise RuntimeError(f"Zep init failed: {e}")

        self._sessions: dict[str, str] = {}

    @property
    def name(self) -> str:
        return "Zep"

    def _get_session(self, session_id: str) -> str:
        if session_id not in self._sessions:
            zep_sid = f"bench-{uuid.uuid4().hex[:12]}"
            try:
                self._client.memory.add_session(
                    session_id=zep_sid, user_id="bench_user"
                )
            except Exception as e:
                raise RuntimeError(f"Zep create session failed: {e}")
            self._sessions[session_id] = zep_sid
        return self._sessions[session_id]

    def add(self, role: str, content: str, session_id: str = "default") -> None:
        try:
            zep_sid = self._get_session(session_id)
            zep_role = "user" if role in ("user", "human") else "assistant"
            self._client.memory.add(
                session_id=zep_sid,
                messages=[Message(role=zep_role, content=content)]
            )
        except Exception as e:
            print(f"    [Zep add warning: {e}]")

    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        try:
            zep_sid = self._get_session(session_id)
            memory = self._client.memory.get(session_id=zep_sid)
            if memory and memory.context:
                return memory.context[:600]
            if memory and memory.messages:
                return "\n".join(
                    f"[{m.role}]: {m.content}"
                    for m in memory.messages[-top_k:]
                )
        except Exception as e:
            return f"[Zep recall error: {e}]"
        return ""

    def extract_patterns(self, session_id: str = "default") -> str:
        try:
            zep_sid = self._get_session(session_id)
            memory = self._client.memory.get(session_id=zep_sid)
            parts = []
            if memory and memory.context:
                parts.append(f"Context: {memory.context[:400]}")
            if memory and hasattr(memory, "facts") and memory.facts:
                parts.append("Facts:\n" + "\n".join(f"- {f}" for f in memory.facts[:6]))
            return "\n".join(parts) if parts else "No patterns extracted yet."
        except Exception as e:
            return f"[Zep pattern error: {e}]"

    def reset(self, session_id: str = "default") -> None:
        zep_sid = self._sessions.get(session_id)
        if zep_sid:
            try:
                self._client.memory.delete(session_id=zep_sid)
            except Exception:
                pass
            del self._sessions[session_id]