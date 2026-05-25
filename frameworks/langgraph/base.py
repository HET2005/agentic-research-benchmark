import os
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parents[2]))

def llm_call(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    from dotenv import load_dotenv
    load_dotenv()

    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if minimax_key:
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=minimax_key,
                base_url="https://api.minimax.io/anthropic",
            )
            resp = client.messages.create(
                model="MiniMax-Text-01",
                max_tokens=max_tokens,
                system=system or "You are a helpful research assistant.",
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
        except Exception as e:
            return f"[LLM ERROR] {e}"

    elif groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
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
        except Exception as e:
            return f"[LLM ERROR] {e}"

    else:
        return f"[MOCK] prompt_hash={hash(prompt) % 99999}"

def search_web(query: str, max_results: int = 6) -> str:
    from tools.ddg_tool import ddg_search
    return ddg_search(query, max_results=max_results)

def search_finance(query: str) -> str:
    from tools.yf_tool import yf_search
    return yf_search(query)

class Timer:
    def __init__(self):
        self._start = None
        self.elapsed = 0.0
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start