"""DRAFT Protocol Configuration."""

import os
from pathlib import Path

# ── Storage ───────────────────────────────────────────────
DB_PATH = Path(os.environ.get("DRAFT_DB_PATH", "~/.draft_protocol/draft.db")).expanduser()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── LLM Provider (optional — enhances classification accuracy) ──
# Supported: "none" (default), "ollama", "openai", "anthropic"
# "openai" works with any OpenAI-compatible API (Together, Groq, LM Studio, etc.)
LLM_PROVIDER = os.environ.get("DRAFT_LLM_PROVIDER", "none")
LLM_MODEL = os.environ.get("DRAFT_LLM_MODEL", "")
EMBED_MODEL = os.environ.get("DRAFT_EMBED_MODEL", "")
API_KEY = os.environ.get("DRAFT_API_KEY", "")
API_BASE = os.environ.get("DRAFT_API_BASE", "")

# Backward compatibility: if old DRAFT_OLLAMA_URL is set, use it
if not API_BASE and os.environ.get("DRAFT_OLLAMA_URL"):
    API_BASE = os.environ["DRAFT_OLLAMA_URL"]

# Auto-detect provider from model name if not explicitly set
if LLM_PROVIDER == "none" and LLM_MODEL:
    if "gpt" in LLM_MODEL or "o1" in LLM_MODEL or "o3" in LLM_MODEL:
        LLM_PROVIDER = "openai"
    elif "claude" in LLM_MODEL:
        LLM_PROVIDER = "anthropic"
    elif LLM_MODEL:
        LLM_PROVIDER = "ollama"  # Default to Ollama for unknown models

# ── Tier Classification Triggers ──────────────────────────
# Keyword-based fast path. LLM classification (if available) handles ambiguous cases.

CONSEQUENTIAL_TRIGGERS = [
    "canonical",
    "governance",
    "constitution",
    "guardian",
    "authority",
    "ip ",
    "intellectual property",
    "classification level",
    "consciousness",
    "self-model",
    "phenomenological",
    "restructure",
    "architecture decision",
    "merge domains",
    "amendment",
    "hard constraint",
    "prohibition",
    "production deployment",
    "security policy",
    "auth modification",
]

STANDARD_TRIGGERS = [
    "implement",
    "specification",
    "draft",
    "build",
    "create",
    "design",
    "analyze",
    "recommend",
    "evaluate",
    "compare",
    "refactor",
    "migrate",
    "integrate",
    "deploy",
    "configure",
    "document",
    "spec",
    "proposal",
    "pipeline",
    "workflow",
    # Security: extraction-pattern triggers (OWASP LLM07)
    "ignore previous instructions",
    "ignore all previous",
    "ignore above",
    "repeat above",
    "repeat everything",
    "verbatim",
    "system prompt",
    "print environment",
    "environment variables",
    "show me your instructions",
    "what are your rules",
    "dump your config",
    "reveal your prompt",
    "debug mode",
]

# ── Dimensions ────────────────────────────────────────────
# D and T are mandatory; R, A, F can be screened out when inapplicable.

MANDATORY_DIMENSIONS = ["D", "T"]

DRAFT_FIELDS = {
    "D": {
        "D1": "What exactly is being created?",
        "D2": "What domain does it belong to?",
        "D3": "What fails without it?",
        "D4": "Replacement test — what existing thing could serve?",
        "D5": "What are the explicit non-goals?",
    },
    "R": {
        "R1": "Who is the human authority source?",
        "R2": "What decisions is this allowed to make?",
        "R3": "What decisions are forbidden?",
        "R4": "What are the stop conditions (need >= 3)?",
        "R5": "What interfaces does it interact with?",
    },
    "A": {
        "A1": "What inputs are allowed?",
        "A2": "What inputs are forbidden?",
        "A3": "What outputs are allowed?",
        "A4": "What outputs are forbidden?",
        "A5": "Provide a correct example.",
        "A6": "Provide an incorrect example.",
    },
    "F": {
        "F1": "Who has change authority?",
        "F2": "What changes are permitted?",
        "F3": "What changes are forbidden?",
        "F4": "What triggers a review?",
    },
    "T": {
        "T1": "How is success defined?",
        "T2": "How is failure defined?",
        "T3": "What review questions apply (need >= 3)?",
        "T4": "What evidence is required?",
    },
}

DIMENSION_SCREEN_QUESTIONS = {
    "D": None,  # Never screened
    "R": "Does this task involve delegated decisions, authority, or operational limits?",
    "A": "Does this task consume or produce specific artifacts (files, data, outputs)?",
    "F": "Does this task have a lifecycle — will it need to change or adapt over time?",
    "T": None,  # Never screened
}

DIMENSION_NAMES = {
    "D": "Define (Existence & ROI)",
    "R": "Rules (Operation & Limits)",
    "A": "Artifacts (Inputs & Outputs)",
    "F": "Flex (Change Without Drift)",
    "T": "Test (Evaluation)",
}
