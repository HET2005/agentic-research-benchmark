import os
import json
from dotenv import load_dotenv

load_dotenv()

# Global tracking for the current run's token usage and cost
SESSION_USAGE = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

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

def llm_call(prompt: str, system: str = "", max_tokens: int = 2048, seed: int = None) -> str:
    providers = []

    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # MiniMax first — sir confirmed it works on his system
    if minimax_key and not minimax_key.startswith("sk-dummy"):
        providers.append(("minimax", minimax_key))
    if groq_key and not groq_key.startswith("sk-dummy"):
        providers.append(("groq", groq_key))
    if openai_key and not openai_key.startswith("sk-dummy"):
        providers.append(("openai", openai_key))
    if anthropic_key and not anthropic_key.startswith("sk-dummy"):
        providers.append(("anthropic", anthropic_key))

    for provider, key in providers:
        try:
            if provider == "minimax":
                import anthropic as anthropic_sdk
                client = anthropic_sdk.Anthropic(
                    api_key=key,
                    base_url="https://api.minimax.io/anthropic",
                )
                resp = client.messages.create(
                    model="MiniMax-Text-01",
                    max_tokens=max_tokens,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}]
                )
                text = resp.content[0].text
                if "base_resp" in text or '"status_code"' in text:
                    raise ValueError("MiniMax returned error payload")
                
                # Usage & Cost
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok = getattr(resp.usage, 'input_tokens', 0)
                    out_tok = getattr(resp.usage, 'output_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok + out_tok) * (0.10 / 1e6))
                    
                return text

            elif provider == "groq":
                from groq import Groq
                client = Groq(api_key=key)
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                kwargs = {"model": "llama-3.1-8b-instant", "max_tokens": max_tokens, "messages": messages}
                if seed is not None:
                    kwargs["seed"] = seed
                
                resp = client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content
                
                # Usage & Cost (Groq 8b: $0.05/1M in, $0.08/1M out)
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok = getattr(resp.usage, 'prompt_tokens', 0)
                    out_tok = getattr(resp.usage, 'completion_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok * 0.05 + out_tok * 0.08) / 1e6)
                    
                return text

            elif provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=key)
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                kwargs = {"model": "gpt-4o-mini", "max_tokens": max_tokens, "messages": messages}
                if seed is not None:
                    kwargs["seed"] = seed
                
                resp = client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content
                
                # Usage & Cost (GPT-4o-mini: $0.15/1M in, $0.60/1M out)
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok = getattr(resp.usage, 'prompt_tokens', 0)
                    out_tok = getattr(resp.usage, 'completion_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok * 0.15 + out_tok * 0.60) / 1e6)
                    
                return text

            elif provider == "anthropic":
                import anthropic as anthropic_sdk
                client = anthropic_sdk.Anthropic(api_key=key)
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}]
                )
                text = resp.content[0].text
                
                # Usage & Cost (Haiku: $1.00/1M in, $5.00/1M out approx)
                if hasattr(resp, 'usage') and resp.usage:
                    in_tok = getattr(resp.usage, 'input_tokens', 0)
                    out_tok = getattr(resp.usage, 'output_tokens', 0)
                    update_usage(in_tok, out_tok, (in_tok * 1.00 + out_tok * 5.00) / 1e6)
                    
                return text

        except Exception:
            continue

    return "[NO_API_KEY] No working provider found."