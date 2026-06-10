import os
import inspect
from functools import wraps
from typing import Any, Callable
from memory import get_memory_provider

# Global placeholder inside runtime worker thread to access memory cleanly anywhere
_CURRENT_MEMORY_PROVIDER = None

def get_current_memory():
    """
    Allows any agent layer or framework tool to instantly grab the active 
    memory layer context without requiring it in the function signature.
    """
    global _CURRENT_MEMORY_PROVIDER
    return _CURRENT_MEMORY_PROVIDER

def with_memory(pipeline_func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator targeted at attaching unified semantic memory providers to runs.
    Inspects target signatures dynamically to avoid keyword collisions.
    """
    @wraps(pipeline_func)
    def wrapper(*args, **kwargs):
        global _CURRENT_MEMORY_PROVIDER
        
        provider = os.getenv("mem0", "in_memory")
        session_id = kwargs.get("run_id") or kwargs.get("session_id") or "benchmark_session_default_2026"
        
        config = {
            "qdrant_path": os.getenv("QDRANT_PATH", "./.cache/qdrant_store"),
            "zep_api_url": os.getenv("ZEP_API_URL", "http://localhost:8000"),
            "zep_api_key": os.getenv("ZEP_API_KEY", "mock_key")
        }
        
        # Instantiate memory provider
        memory_engine = get_memory_provider(provider, session_id, config)
        
        # Save reference globally for internal agent tools to capture via helper
        _CURRENT_MEMORY_PROVIDER = memory_engine
        
        # Check if the pipeline run() function explicitly accepts 'memory'
        sig = inspect.signature(pipeline_func)
        if "memory" in sig.parameters:
            kwargs["memory"] = memory_engine
            
        try:
            return pipeline_func(*args, **kwargs)
        finally:
            # Prevent context leaking between consecutive bench worker seeds
            _CURRENT_MEMORY_PROVIDER = None
            
    return wrapper