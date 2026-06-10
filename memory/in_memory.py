from typing import Any, Dict, List
from .base_memory import BaseMemory

class InMemoryStore(BaseMemory):
    """
    Lightweight runtime isolated semantic buffer tracking contextual data state arrays inside runtime memory.
    """
    def __init__(self, session_id: str, config: Dict[str, Any] = None):
        super().__init__(session_id, config)
        self.storage: List[Dict[str, Any]] = []

    def add_memories(self, text: str, metadata: Dict[str, Any] = None) -> None:
        self.storage.append({
            "content": text,
            "metadata": metadata or {},
            "session_id": self.session_id
        })

 # Edit memory/in_memory.py
    def get_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        results = [mem for mem in self.storage if mem["session_id"] == self.session_id]
    
    # ADD THIS LINE TO DEBUG:
        print(f"[DEBUG] Memory retrieved {len(results[-limit:])} items for query: {query}")
    
        return results[-limit:]
    def clear_memories(self) -> None:
        self.storage = [mem for mem in self.storage if mem["session_id"] != self.session_id]