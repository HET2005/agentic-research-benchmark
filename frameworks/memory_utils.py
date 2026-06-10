import functools

def with_memory(func):
    @functools.wraps(func)
    def wrapper(question: str, run_id: str = "default", seed: int = 0, memory=None, **kwargs):
        original_question = question
        if memory:
            recalled = memory.recall(question, session_id=run_id)
            if recalled:
                question = f"{question}\n\n[Relevant Past Context]:\n{recalled}"
        
        result = func(question, run_id=run_id, seed=seed, **kwargs)
        
        if memory:
            memory.add("user", original_question, session_id=run_id)
            memory.add("assistant", result["answer"], session_id=run_id)
            result["question"] = original_question
            
        return result
    return wrapper
