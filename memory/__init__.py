import os
from .base_memory import BaseMemory
from .in_memory import InMemoryStore

__all__ = ['BaseMemory', 'InMemoryStore', 'Mem0Memory', 'ZepMemory', 'get_memory_provider']

try:
    from .mem0_memory import Mem0Memory
except ImportError:
    class Mem0Memory:
        def __init__(self, *args, **kwargs):
            raise ImportError("mem0 backend missing from target environment context.")

try:
    from .zep_memory import ZepMemory
except ImportError:
    class ZepMemory:
        def __init__(self, *args, **kwargs):
            raise ImportError("zep-python client is required to connect to dynamic server backends.")


def get_memory_provider(provider_name: str, session_id: str, config: dict = None) -> BaseMemory:
    """
    Factory builder resolving the target context storage strategy seamlessly.
    """
    if not provider_name:
        provider_name = "in_memory"
        
    p_low = str(provider_name).lower().strip()
    
    if p_low in ['in_memory', 'inmemory', 'local', 'none', 'default']:
        return InMemoryStore(session_id=session_id, config=config)
    elif p_low == 'mem0':
        return Mem0Memory(session_id=session_id, config=config)
    elif p_low in ['zep', 'zep_memory']:
        return ZepMemory(session_id=session_id, config=config)
    else:
        # Graceful fallback instead of program termination crashing the process
        print(f"[-] Warning: Strategy '{provider_name}' unrecognized. Defaulting safely to InMemoryStore context.")
        return InMemoryStore(session_id=session_id, config=config)