"""LLM Provider Abstraction — Use any AI backend for enhanced governance.

Supported providers:
  - none:      Keyword heuristics only (default, zero dependencies)
  - ollama:    Local LLM via Ollama HTTP API
  - openai:    OpenAI-compatible APIs (OpenAI, Azure, Together, Groq, LM Studio, etc.)
  - anthropic: Anthropic Claude API

All providers implement two operations:
  - chat(): Send a prompt, get structured JSON back
  - embed(): Get a vector embedding for text

Set via environment variables:
  DRAFT_LLM_PROVIDER=ollama|openai|anthropic|none
  DRAFT_LLM_MODEL=llama3.2:3b|gpt-4o-mini|claude-sonnet-4-20250514|...
  DRAFT_EMBED_MODEL=nomic-embed-text|text-embedding-3-small|...
  DRAFT_API_KEY=sk-...  (required for cloud providers)
  DRAFT_API_BASE=https://...  (optional custom endpoint)
"""

import json
import urllib.request

from draft_protocol.config import (
    API_BASE,
    API_KEY,
    EMBED_MODEL,
    LLM_MODEL,
    LLM_PROVIDER,
)


def _post(url: str, data: dict, headers: dict, timeout: int = 30) -> dict:
    """HTTP POST with JSON body. Returns parsed response."""
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result: dict = json.loads(resp.read())
        return result


# ── Provider: Ollama ──────────────────────────────────────


def _ollama_chat(prompt: str, schema: dict, timeout: int = 30) -> dict | None:
    base = API_BASE or "http://localhost:11434"
    resp = _post(
        f"{base}/api/chat",
        {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": schema,
            "options": {"temperature": 0.1, "num_predict": 500},
        },
        {"Content-Type": "application/json"},
        timeout=timeout,
    )
    content = resp.get("message", {}).get("content", "").strip()
    if not content:
        return None
    parsed: dict = json.loads(content)  # type: ignore[assignment]
    return parsed


def _ollama_embed(text: str, timeout: int = 30) -> list:
    base = API_BASE or "http://localhost:11434"
    resp = _post(
        f"{base}/api/embed",
        {"model": EMBED_MODEL, "input": text},
        {"Content-Type": "application/json"},
        timeout=timeout,
    )
    embs = resp.get("embeddings", [])
    return embs[0] if embs else []


# ── Provider: OpenAI-compatible ───────────────────────────


def _openai_chat(prompt: str, schema: dict, timeout: int = 30) -> dict | None:
    base = API_BASE or "https://api.openai.com/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    # Build JSON schema instruction since not all OpenAI-compatible APIs support response_format
    schema_instruction = f"\n\nRespond ONLY with valid JSON matching this schema, no other text:\n{json.dumps(schema)}"
    resp = _post(
        f"{base}/chat/completions",
        {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt + schema_instruction}],
            "temperature": 0.1,
            "max_tokens": 500,
        },
        headers,
        timeout=timeout,
    )
    content = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if not content:
        return None
    parsed: dict = json.loads(content)  # type: ignore[assignment]
    return parsed


def _openai_embed(text: str, timeout: int = 30) -> list:
    base = API_BASE or "https://api.openai.com/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    resp = _post(
        f"{base}/embeddings",
        {"model": EMBED_MODEL, "input": text},
        headers,
        timeout=timeout,
    )
    data = resp.get("data", [])
    return data[0].get("embedding", []) if data else []


# ── Provider: Anthropic ───────────────────────────────────


def _anthropic_chat(prompt: str, schema: dict, timeout: int = 30) -> dict | None:
    base = API_BASE or "https://api.anthropic.com/v1"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }
    schema_instruction = f"\n\nRespond ONLY with valid JSON matching this schema, no other text:\n{json.dumps(schema)}"
    resp = _post(
        f"{base}/messages",
        {
            "model": LLM_MODEL,
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt + schema_instruction}],
            "temperature": 0.1,
        },
        headers,
        timeout=timeout,
    )
    content_blocks = resp.get("content", [])
    text = ""
    for block in content_blocks:
        if block.get("type") == "text":
            text += block.get("text", "")
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if not text:
        return None
    parsed: dict = json.loads(text)  # type: ignore[assignment]
    return parsed


def _anthropic_embed(text: str, timeout: int = 30) -> list:
    # Anthropic doesn't offer embeddings — fall back to empty
    return []


# ── Provider Dispatch ─────────────────────────────────────

_CHAT_PROVIDERS = {
    "ollama": _ollama_chat,
    "openai": _openai_chat,
    "anthropic": _anthropic_chat,
}

_EMBED_PROVIDERS = {
    "ollama": _ollama_embed,
    "openai": _openai_embed,
    "anthropic": _anthropic_embed,
}


def llm_available() -> bool:
    """True if an LLM provider is configured and has a model set."""
    return bool(LLM_PROVIDER and LLM_PROVIDER != "none" and LLM_MODEL)


def embed_available() -> bool:
    """True if an embedding provider is configured and has a model set."""
    return bool(LLM_PROVIDER and LLM_PROVIDER != "none" and EMBED_MODEL)


def chat(prompt: str, schema: dict, timeout: int = 30) -> dict | None:
    """Send a structured prompt to the configured LLM provider.

    Returns parsed dict matching schema, or None on any failure.
    """
    if not llm_available():
        return None
    fn = _CHAT_PROVIDERS.get(LLM_PROVIDER)
    if not fn:
        return None
    try:
        result = fn(prompt, schema, timeout)
        return result if isinstance(result, dict) else None
    except Exception:
        return None


def embed(text: str, timeout: int = 30) -> list:
    """Get embedding vector for text from the configured provider.

    Returns list of floats, or empty list on any failure.
    """
    if not embed_available():
        return []
    fn = _EMBED_PROVIDERS.get(LLM_PROVIDER)
    if not fn:
        return []
    try:
        return fn(text, timeout)
    except Exception:
        return []
