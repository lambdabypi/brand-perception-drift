"""
providers.py

Real API wrappers. No mocking, no fixtures -- these hit live services.
You need two free API keys for this to run:

  GROQ_API_KEY    -> https://console.groq.com/keys (free tier, generous limits)
  TAVILY_API_KEY  -> https://tavily.com (free tier, 1000 searches/month)

Put both in a .env file (see .env.example) or export them as env vars.
"""

import os
from groq import Groq
from tavily import TavilyClient

# Checked against https://console.groq.com/docs/deprecations on Jul 16 2026.
# llama-3.3-70b-versatile, llama-3.1-8b-instant, and gemma2-9b-it are all
# deprecated/decommissioned as of this writing. If one of these 404s or
# throws model_decommissioned again by the time you run this, check that
# page again -- Groq's lineup moves fast and this list WILL go stale.
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
]


def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys")
    return Groq(api_key=api_key)


def get_tavily_client() -> TavilyClient:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not set. Get a free key at https://tavily.com")
    return TavilyClient(api_key=api_key)


def _reasoning_kwargs(model: str) -> dict:
    """gpt-oss and qwen3.6 on Groq are reasoning models that spend part of
    their token budget on hidden/inline reasoning before writing a final
    answer. Left uncontrolled, a low max_tokens can get fully consumed by
    reasoning, leaving an empty or truncated-mid-thought answer -- which is
    exactly what happened on the first run. Dialing reasoning down (and
    giving more room overall) fixes that without changing what we're asking.
    Per https://console.groq.com/docs/api-reference (checked Jul 2026):
    gpt-oss models accept low/medium/high (no 'none'); qwen3 models accept
    none/default. Re-check this if you swap in different models later.
    """
    if "gpt-oss" in model:
        return {"reasoning_effort": "low"}
    if "qwen" in model:
        return {"reasoning_effort": "none"}
    return {}


def ask_groq(client: Groq, model: str, prompt: str, temperature: float = 0.2) -> str:
    """Single-turn completion, no context injected. This is the 'parametric
    only' condition -- whatever the model already believes from training."""
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=1200,
        **_reasoning_kwargs(model),
    )
    return completion.choices[0].message.content


def ask_groq_with_context(client: Groq, model: str, prompt: str, context: str, temperature: float = 0.2) -> str:
    """Same question, but with a context block injected -- either ambient
    web search results or a corrected canonical profile. This simulates a
    retrieval-augmented agent, without needing a real live registry."""
    system = (
        "Answer the user's question using ONLY the information in the "
        "CONTEXT block below. If the context doesn't cover something, say "
        "you don't have that information rather than guessing.\n\nCONTEXT:\n"
        f"{context}"
    )
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=1200,
        **_reasoning_kwargs(model),
    )
    return completion.choices[0].message.content


def search_web(client: TavilyClient, brand_name: str) -> str:
    """Ambient web search -- what a naive RAG agent would see, with no
    curation. Returns concatenated snippets, capped to keep prompts short."""
    query = f"{brand_name} company founded headquarters pricing product"
    results = client.search(query=query, max_results=5)
    snippets = []
    for r in results.get("results", []):
        title = r.get("title", "")
        content = r.get("content", "")[:400]
        snippets.append(f"[{title}]\n{content}")
    return "\n\n".join(snippets) if snippets else "(no search results returned)"
