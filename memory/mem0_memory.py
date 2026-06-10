from .base_memory import BaseMemoryStore
import os

class Mem0MemoryStore(BaseMemoryStore):
    def __init__(self, run_id: str):
        super().__init__(run_id)
        try:
            from mem0 import Memory
            # Simple local memory config so we don't rely on cloud vectors
            config = {
                "vector_store": {
                    "provider": "chroma",
                    "config": {"collection_name": "agentic_bench_mem"}
                }
            }
            self.memory = Memory.from_config(config_dict=config)
            self.active = True
        except ImportError:
            print("[WARN] mem0 package not installed. Memory disabled.")
            self.active = False
            self.backup = []

    def add_message(self, role: str, content: str):
        if self.active:
            self.memory.add(content, user_id=self.run_id, metadata={"role": role})
        else:
            self.backup.append({"role": role, "content": content})

    def get_context(self, query: str = "") -> str:
        if self.active:
            # Mem0 semantic search
            results = self.memory.search(query or "general context", user_id=self.run_id)
            if results:
                return "\n".join([r['memory'] for r in results])
            return ""
        return "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.backup])

    def get_messages(self) -> list:
        if self.active:
            mems = self.memory.get_all(user_id=self.run_id)
            return [{"role": "memory", "content": m["memory"]} for m in mems]
        return self.backup

    def clear(self):
        if self.active:
            self.memory.delete_all(user_id=self.run_id)
        else:
            self.backup = []