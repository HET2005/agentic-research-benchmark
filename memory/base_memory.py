from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseMemory(ABC):
    """
    Base abstraction interface structure separating runtime backends from agent pipelines.
    """
    def __init__(self, session_id: str, config: Dict[str, Any] = None):
        self.session_id = session_id
        self.config = config or {}

    @abstractmethod
    def add_memories(self, text: str, metadata: Dict[str, Any] = None) -> None:
        """Saves memory contextual metadata fields safely."""
        pass

    @abstractmethod
    def get_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves history using semantic matching parameters."""
        pass

    @abstractmethod
    def clear_memories(self) -> None:
        """Purges indices matching tracking keys."""
        pass