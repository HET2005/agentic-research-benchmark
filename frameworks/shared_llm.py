"""
frameworks/shared_llm.py
Single shared LLM caller used by all frameworks.
Falls through all providers until one works.
"""
import os
from dotenv import load_dotenv
load_dotenv()

def llm_call(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    providers = []

    if groq_key:
        providers.append(("groq", groq_key))
    if minimax_key:
        providers.append(("minimax", minimax_key))
    if anthropic_key and not anthropic_key.startswith("sk-dummy"):
        providers.append(("anthropic", anthropic_key))
    if openai_key and not openai_key.startswith("sk-dummy"):
        providers.append(("openai", openai_key))

    for provider, key in providers:
        try:
            if provider == "groq":
                from groq import Groq
                client = Groq(api_key=key)
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    max_tokens=max_tokens,
                    messages=messages,
                )
                return resp.choices[0].message.content

            elif provider == "minimax":
                import anthropic
                client = anthropic.Anthropic(
                    api_key=key,
                    base_url="https://api.minimax.io/anthropic",
                )
                resp = client.messages.create(
                    model="MiniMax-Text-01",
                    max_tokens=max_tokens,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text

            elif provider == "anthropic":
                import anthropic
                client = anthropic.Anthropic(api_key=key)
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text

            elif provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=key)
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=max_tokens,
                    messages=messages,
                )
                return resp.choices[0].message.content

        except Exception:
            continue  # Try next provider

    return "[NO_API_KEY] No working provider found."