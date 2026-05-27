# frameworks/shared_llm.py
import os
import json
from dotenv import load_dotenv
load_dotenv()

# BUG 7 & 8 FIX: Accept seed parameter and strictly order fallback (OpenAI -> Anthropic -> Groq -> MiniMax)
def llm_call(prompt: str, system: str = "", max_tokens: int = 2048, seed: int = None) -> str:
    providers = []
    
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")

    if openai_key and not openai_key.startswith("sk-dummy"): providers.append(("openai", openai_key))
    if anthropic_key and not anthropic_key.startswith("sk-dummy"): providers.append(("anthropic", anthropic_key))
    if groq_key and not groq_key.startswith("sk-dummy"): providers.append(("groq", groq_key))
    if minimax_key and not minimax_key.startswith("sk-dummy"): providers.append(("minimax", minimax_key))

    for provider, key in providers:
        try:
            if provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=key)
                messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}] if system else [{"role": "user", "content": prompt}]
                kwargs = {"model": "gpt-4o-mini", "max_tokens": max_tokens, "messages": messages}
                if seed is not None: kwargs["seed"] = seed
                return client.chat.completions.create(**kwargs).choices[0].message.content

            elif provider == "anthropic":
                import anthropic
                client = anthropic.Anthropic(api_key=key)
                return client.messages.create(
                    model="claude-3-haiku-20240307", max_tokens=max_tokens,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}]
                ).content[0].text

            elif provider == "groq":
                from groq import Groq
                client = Groq(api_key=key)
                messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}] if system else [{"role": "user", "content": prompt}]
                kwargs = {"model": "llama-3.1-8b-instant", "max_tokens": max_tokens, "messages": messages}
                if seed is not None: kwargs["seed"] = seed
                return client.chat.completions.create(**kwargs).choices[0].message.content

            elif provider == "minimax":
                import anthropic
                client = anthropic.Anthropic(api_key=key, base_url="https://api.minimax.io/anthropic")
                resp = client.messages.create(
                    model="MiniMax-Text-01", max_tokens=max_tokens,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}]
                ).content[0].text
                
                # BUG 5 FIX: Detect soft-fails from MiniMax API and trigger fallthrough
                if "base_resp" in resp or '"status_code"' in resp:
                    raise ValueError("MiniMax returned an error payload instead of completion.")
                return resp

        except Exception as e:
            continue  # Try next provider

    return "[NO_API_KEY] No working provider found."