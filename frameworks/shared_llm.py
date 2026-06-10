import os
from dotenv import load_dotenv

load_dotenv()

# Global trackers for usage and memory
SESSION_USAGE = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
GLOBAL_MEMORY = []

def reset_usage():
    global SESSION_USAGE
    SESSION_USAGE = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

def get_usage():
    return SESSION_USAGE.copy()

def update_usage(in_tok: int, out_tok: int, cost: float):
    global SESSION_USAGE
    SESSION_USAGE["input_tokens"] += in_tok
    SESSION_USAGE["output_tokens"] += out_tok
    SESSION_USAGE["cost"] += cost

def reset_memory():
    global GLOBAL_MEMORY
    GLOBAL_MEMORY = []

def format_messages_safely(system: str, prompt: str, history: list) -> list:
    """Merges consecutive messages of the same role to prevent Anthropic/MiniMax API crashes."""
    raw_msgs = []
    if system:
        raw_msgs.append({"role": "system", "content": system})
    
    raw_msgs.extend(history)
    raw_msgs.append({"role": "user", "content": prompt})

    merged = []
    for msg in raw_msgs:
        if not merged:
            merged.append(msg)
        elif merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n\n" + msg["content"]
        else:
            merged.append(msg)
    return merged

def llm_call(prompt: str, system: str = "", max_tokens: int = 2048, seed: int = None, use_memory: bool = False) -> str:
    global GLOBAL_MEMORY
    providers = []

    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if minimax_key and not minimax_key.startswith("sk-dummy"): providers.append(("minimax", minimax_key))
    if groq_key and not groq_key.startswith("sk-dummy"): providers.append(("groq", groq_key))
    if openai_key and not openai_key.startswith("sk-dummy"): providers.append(("openai", openai_key))
    if anthropic_key and not anthropic_key.startswith("sk-dummy"): providers.append(("anthropic", anthropic_key))

    # Prepare safe context window (limit to last 10 turns to save tokens)
    history = GLOBAL_MEMORY[-10:] if use_memory else []
    safe_messages = format_messages_safely(system, prompt, history)

    for provider, key in providers:
        try:
            if provider == "minimax":
                import anthropic as anthropic_sdk
                client = anthropic_sdk.Anthropic(api_key=key, base_url="https://api.minimax.io/anthropic")
                resp = client.messages.create(
                    model="MiniMax-Text-01",
                    max_tokens=max_tokens,
                    system=system or "You are a helpful assistant.",
                    messages=[m for m in safe_messages if m["role"] != "system"]
                )
                text = resp.content[0].text
                if "base_resp" in text or '"status_code"' in text: raise ValueError("MiniMax error")
                
                if hasattr(resp, 'usage') and resp.usage:
                    update_usage(getattr(resp.usage, 'input_tokens', 0), getattr(resp.usage, 'output_tokens', 0), 0.0)
                
                if use_memory:
                    GLOBAL_MEMORY.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": text}])
                return text

            elif provider == "groq":
                from groq import Groq
                client = Groq(api_key=key)
                kwargs = {"model": "llama-3.1-8b-instant", "max_tokens": max_tokens, "messages": safe_messages}
                if seed is not None: kwargs["seed"] = seed
                
                resp = client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content
                
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok, out_tok = getattr(resp.usage, 'prompt_tokens', 0), getattr(resp.usage, 'completion_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok * 0.05 + out_tok * 0.08) / 1e6)
                
                if use_memory:
                    GLOBAL_MEMORY.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": text}])
                return text

            elif provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=key)
                kwargs = {"model": "gpt-4o-mini", "max_tokens": max_tokens, "messages": safe_messages}
                if seed is not None: kwargs["seed"] = seed
                
                resp = client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content
                
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok, out_tok = getattr(resp.usage, 'prompt_tokens', 0), getattr(resp.usage, 'completion_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok * 0.15 + out_tok * 0.60) / 1e6)
                
                if use_memory:
                    GLOBAL_MEMORY.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": text}])
                return text

            elif provider == "anthropic":
                import anthropic as anthropic_sdk
                client = anthropic_sdk.Anthropic(api_key=key)
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    system=system or "You are a helpful assistant.",
                    messages=[m for m in safe_messages if m["role"] != "system"]
                )
                text = resp.content[0].text
                
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok, out_tok = getattr(resp.usage, 'input_tokens', 0), getattr(resp.usage, 'output_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok * 1.00 + out_tok * 5.00) / 1e6)
                
                if use_memory:
                    GLOBAL_MEMORY.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": text}])
                return text

        except Exception:
            continue

    return "[NO_API_KEY] No working provider found."