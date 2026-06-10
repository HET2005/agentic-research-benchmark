# memory/base_memory.py
from abc import ABC, abstractmethod
from typing import Optional

class BaseMemory(ABC):
    """
    Abstract interface every memory solution must implement.
    Two capabilities under test:
      - add()     : store a conversation turn
      - recall()  : retrieve relevant context given a query
      - extract_patterns() : summarise recurring entities / themes seen so far
    """

    @abstractmethod
    def add(self, role: str, content: str, session_id: str = "default") -> None:
        """Store one conversation turn."""

    @abstractmethod
    def recall(self, query: str, session_id: str = "default", top_k: int = 3) -> str:
        """Return the most relevant past context for the query as a string."""

    @abstractmethod
    def extract_patterns(self, session_id: str = "default") -> str:
        """Return a string describing recurring entities / themes in the session."""

    @abstractmethod
    def reset(self, session_id: str = "default") -> None:
        """Clear all memory for a session."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable solution name."""