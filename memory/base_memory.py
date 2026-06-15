# memory/base_memory.py
from abc import ABC, abstractmethod


class BaseMemory(ABC):
    """Abstract interface for all memory solutions."""

    @abstractmethod
    def add(self, role: str, content: str, session_id: str = "default") -> None:
        """Store one conversation turn."""

    @abstractmethod
    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        """Return most relevant past context for the query as a string."""

    @abstractmethod
    def extract_patterns(self, session_id: str = "default") -> str:
        """Return recurring entities / themes seen in the session."""

    @abstractmethod
    def reset(self, session_id: str = "default") -> None:
        """Clear all memory for a session."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable solution name."""