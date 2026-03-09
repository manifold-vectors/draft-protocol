"""DRAFT Protocol Engine — Intake Governance Intelligence.

Features:
  1. Tier classification — keyword fast-path + optional LLM semantic classification
  2. Field assessment — optional embedding-based cosine similarity or keyword heuristics
  3. Context-aware suggestions — optional LLM scaffolds or static templates
  4. Classification confidence scoring — 0.0-1.0 on all assessments
  5. Graceful degradation — works without any LLM, better with one
  6. Closed session guards — all operations reject closed sessions (M1.3)
  7. Tier enum validation — rejects invalid tier strings (M1.4)
  8. Context enrichment — gate PASS returns full dimensional mapping (M1.5)

Supports any LLM provider via DRAFT_LLM_PROVIDER env var:
  ollama, openai (+ compatible APIs), anthropic, or none (keyword-only).
"""

import contextlib
import math
from typing import Any

from draft_protocol import providers, storage
from draft_protocol.config import (
    ALL_TIERS,
    CONSEQUENTIAL_TRIGGERS,
    DIMENSION_NAMES,
    DIMENSION_SCREEN_QUESTIONS,
    DRAFT_FIELDS,
    LEGACY_MAP,
    LOOKUP_TRIGGERS,
    MANDATORY_DIMENSIONS,
    MULTI_TRIGGERS,
    STANDARD_TRIGGERS,
    TIER_ASSUMPTIONS,
    TIER_CEREMONY,
    TIER_TO_LEGACY,
    TRIVIAL_PATTERNS,
)
from draft_protocol.extension_points import get_classify_hook, get_post_gate_hook

# ── M1.3: Closed Session Guard ───────────────────────────

_CLOSED_SESSION_ERROR = "Session {sid} is closed. Start new session with draft_intake."


def _check_open(session_id: str) -> dict | None:
    """Return error dict if session is closed or missing, else None."""
    if storage.is_session_closed(session_id):
        return {"error": _CLOSED_SESSION_ERROR.format(sid=session_id)}
    return None


# ── LLM Schemas ───────────────────────────────────────────

TIER_SCHEMA = {
    "type": "object",
    "properties": {
        "tier": {"type": "string", "enum": [
            "TRIVIAL", "LOOKUP", "TASK", "MULTI", "CONSEQUENTIAL",
            "CASUAL", "STANDARD",  # Legacy compat
        ]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
    "required": ["tier", "confidence", "reasoning"],
}

FIELD_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["SATISFIED", "AMBIGUOUS", "MISSING"]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "extracted": {"type": "string"},
        "reasoning": {"type": "string"},
    },
    "required": ["status", "confidence", "extracted"],
}

SCREEN_SCHEMA = {
    "type": "object",
    "properties": {
        "applicable": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
    "required": ["applicable", "confidence"],
}

SUGGESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestion": {"type": "string"},
        "example": {"type": "string"},
    },
    "required": ["suggestion"],
}


# ── Feature Detection ─────────────────────────────────────


def _llm_available() -> bool:
    """Check if LLM provider is configured."""
    return providers.llm_available()


def _embed_available() -> bool:
    """Check if embedding provider is configured."""
    return providers.embed_available()


# ── Embedding Helpers ─────────────────────────────────────


def _embed(text: str) -> list:
    return providers.embed(text)


def _cosine_sim(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    result: float = dot / (na * nb)
    return result


def _llm_call(prompt: str, schema: dict, timeout: int = 30) -> dict | None:
    """Structured LLM call via configured provider. Returns parsed dict or None."""
    return providers.chat(prompt, schema, timeout)


# ── Tier Classification ───────────────────────────────────


def classify_tier(message: str) -> tuple[str, str, float]:
    """Classify message into 5 governance tiers (GDE v1 port).

    Priority: T4 CONSEQUENTIAL > T3 MULTI > T2 TASK > T1 LOOKUP > T0 TRIVIAL.
    Returns (tier, reasoning, confidence).
    Backward compatible: CASUAL/STANDARD still accepted as overrides.
    """
    message = str(message).strip() if message is not None else ""
    if not message:
        return "REJECTED", "Empty or whitespace-only message — cannot classify", 0.0

    # Extension point: custom classifier (e.g., GDE) gets first shot
    hook = get_classify_hook()
    if hook is not None:
        hook_result = hook(message)
        if hook_result is not None:
            return hook_result

    lower = message.lower()
    words = message.split()
    word_count = len(words)

    # ── T4: CONSEQUENTIAL (governance, canonical, IP, security) ──
    matched = [t for t in CONSEQUENTIAL_TRIGGERS if t in lower]
    if matched:
        return "CONSEQUENTIAL", f"T4 keyword: {matched[0]}", 0.95

    # ── T3: MULTI (infrastructure, cross-service, scope operations) ──
    matched = [t for t in MULTI_TRIGGERS if t in lower]
    if matched:
        return "MULTI", f"T3 keyword: {matched[0]}", 0.85

    # Multi-file/multi-system pattern detection
    import re
    multi_pattern = re.compile(
        r"(?:\d+\s*(?:files?|changes?|modifications?))"
        r"|(?:(?:across|multiple|several)\s+(?:files?|services?|systems?|collections?))",
        re.IGNORECASE,
    )
    if multi_pattern.search(message):
        return "MULTI", "Multi-file or cross-service operation detected", 0.80

    # ── T2: TASK (single write/edit/create, standard work) ──
    matched = [t for t in STANDARD_TRIGGERS if t in lower]
    if matched:
        return "TASK", f"T2 keyword: {matched[0]}", 0.85

    # LLM semantic classification for ambiguous messages
    if _llm_available() and word_count > 3:
        prompt = f"""Classify this user message for an AI governance system.

TRIVIAL = greetings, thanks, "continue", acknowledgments (1-3 words, no action)
LOOKUP = questions, status checks, reads, verifications
TASK = single write/edit/create, building, implementing, modifying
MULTI = multiple files/systems, infrastructure, migrations, cross-service
CONSEQUENTIAL = governance changes, architecture, production, security, IP-sensitive

Message: {message[:500]}"""

        result = _llm_call(prompt, TIER_SCHEMA, timeout=20)
        if result and result.get("tier") in ALL_TIERS:
            return result["tier"], result.get("reasoning", "LLM classification"), result.get("confidence", 0.7)
        # Also accept legacy tier names from LLM
        if result and result.get("tier") in LEGACY_MAP:
            mapped = LEGACY_MAP[result["tier"]]
            return mapped, result.get("reasoning", "LLM classification (legacy mapped)"), result.get("confidence", 0.7)

    # ── T1: LOOKUP (questions, status checks) ──
    matched = [t for t in LOOKUP_TRIGGERS if t in lower]
    if matched:
        return "LOOKUP", f"T1 keyword: {matched[0]}", 0.80

    # ── T0: TRIVIAL (acknowledgments, greetings) ──
    if lower.rstrip(".!?,") in TRIVIAL_PATTERNS or lower in TRIVIAL_PATTERNS:
        return "TRIVIAL", f"Acknowledgment: '{lower[:20]}'", 0.95

    if word_count <= 3:
        return "TRIVIAL", f"Short message ({word_count} words), no action verb", 0.70

    # ── Fallback: length heuristic ──
    if word_count > 50:
        return "TASK", f"Long message ({word_count} words), defaulting to TASK", 0.50

    return "LOOKUP", f"No strong signal ({word_count} words), defaulting to LOOKUP", 0.40


def resolve_tier_override(override: str) -> str:
    """Resolve a tier override to a valid 5-tier name. Accepts legacy names."""
    upper = override.upper().strip()
    if upper in ALL_TIERS:
        return upper
    if upper in LEGACY_MAP:
        return LEGACY_MAP[upper]
    return ""


def get_legacy_tier(tier: str) -> str:
    """Map 5-tier name to legacy CASUAL/STANDARD/CONSEQUENTIAL."""
    return TIER_TO_LEGACY.get(tier, "STANDARD")


def get_ceremony_depth(tier: str) -> str:
    """Get the DRAFT ceremony depth for a tier."""
    return TIER_CEREMONY.get(tier, "visible")


def should_escalate(session: dict) -> tuple[str, str] | None:
    """Check if session should auto-escalate based on ambiguity count."""
    dims = session.get("dimensions", {})
    ambiguous_count = 0
    for _dim_key, fields in dims.items():
        if not isinstance(fields, dict) or fields.get("_screened"):
            continue
        for field_key, state in fields.items():
            if field_key.startswith("_"):
                continue
            if isinstance(state, dict) and state.get("status") == "AMBIGUOUS":
                ambiguous_count += 1

    tier = session["tier"]
    if ambiguous_count > 2 and tier in ("TRIVIAL", "LOOKUP"):
        return "TASK", f"Multiple ambiguous fields ({ambiguous_count})"
    if ambiguous_count > 3 and tier == "TASK":
        return "MULTI", f"Many ambiguous fields ({ambiguous_count})"
    if ambiguous_count > 4 and tier == "MULTI":
        return "CONSEQUENTIAL", f"High ambiguity count ({ambiguous_count})"
    # Legacy compat
    if ambiguous_count > 2 and tier == "CASUAL":
        return "TASK", f"Multiple ambiguous fields ({ambiguous_count})"
    if ambiguous_count > 4 and tier == "STANDARD":
        return "CONSEQUENTIAL", f"Many ambiguous fields ({ambiguous_count})"
    return None


# ── Field Assessment ──────────────────────────────────────

_field_question_embeddings: dict[str, list] = {}


def _get_field_embedding(field_key: str) -> list:
    """Embed field question + answer-form keywords for better matching."""
    if field_key not in _field_question_embeddings:
        for _dim_key, fields in DRAFT_FIELDS.items():
            if field_key in fields:
                question = fields[field_key]
                enrichment = _field_enrichment(field_key)
                _field_question_embeddings[field_key] = _embed(f"{question} {enrichment}")
                break
    return _field_question_embeddings.get(field_key, [])


def _field_enrichment(field_key: str) -> str:
    """Answer-form templates for better question-to-context cosine similarity."""
    return {
        "D1": "We are building a product, system, tool, service, application, dashboard, platform, engine, pipeline",
        "D2": "This belongs to the domain of governance, security, data, AI, infrastructure, compliance, operations",
        "D3": "Without this, the following would fail or be blocked: downstream systems depend on this component",
        "D4": "The existing alternatives include current solutions, workarounds, and replacements that could serve",
        "D5": "This is explicitly not about the following non-goals and out of scope items we will exclude",
        "R1": "The human authority and decision maker responsible for approving this is the founder, lead, manager",
        "R2": "This system is allowed and permitted to perform the following authorized operations and actions",
        "R3": "This system is forbidden and prohibited from performing the following restricted actions",
        "R4": "The system must stop and halt when these abort conditions and safety limits are reached",
        "R5": "This interfaces and connects with the following APIs, systems, integrations, and services",
        "A1": "The system accepts and receives the following inputs: data, files, parameters, requests, queries",
        "A2": "The system must reject and block the following forbidden and invalid inputs",
        "A3": "The system produces and generates the following outputs: responses, files, reports, artifacts",
        "A4": "The system must never produce the following forbidden and invalid outputs",
        "A5": "A correct example of expected output looks like this",
        "A6": "An incorrect and wrong example that should be avoided looks like this",
        "F1": "The authority to change and modify this system belongs to the following people and roles",
        "F2": "The following changes, modifications, and updates are permitted and allowed",
        "F3": "The following changes are frozen, immutable, locked, and forbidden from modification",
        "F4": "A review is triggered when the following conditions, changes, or audit thresholds are met",
        "T1": "Success is defined as: the system works correctly, all tests pass, requirements are verified",
        "T2": "Failure is defined as: the system fails, produces errors, rejects valid input, or is broken",
        "T3": "The review questions to verify include: does the output meet requirements, is it auditable",
        "T4": "The required evidence and proof includes: test results, artifacts, and verification data",
    }.get(field_key, "")


def map_dimensions(session_id: str, context: str) -> dict:
    """Map DRAFT dimensions against user context using LLM or heuristics."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if not context or not context.strip():
        storage.log_audit(session_id, "draft_map", "REJECTED", "Empty or whitespace-only context")
        return {"error": "Cannot map dimensions with empty context. Provide task description."}

    use_llm = _llm_available()
    dimensions = session.get("dimensions", {})
    context_embedding = _embed(context[:2000]) if not use_llm else []

    for dim_key, fields in DRAFT_FIELDS.items():
        if dim_key not in dimensions:
            dimensions[dim_key] = {}

        if dim_key not in MANDATORY_DIMENSIONS:
            if use_llm:
                applicable = _screen_dimension_llm(dim_key, context)
            else:
                applicable = _context_suggests_applicable(dim_key, context)
            if not applicable:
                dimensions[dim_key] = {
                    "_screened": True,
                    "_reason": f"{DIMENSION_NAMES[dim_key]} not applicable",
                }
                continue

        for field_key, question in fields.items():
            if field_key in dimensions[dim_key] and dimensions[dim_key][field_key].get("status") == "CONFIRMED":
                continue

            if use_llm:
                status = _assess_field_llm(field_key, question, context)
            else:
                status = _assess_field_embedding(field_key, question, context, context_embedding)

            dimensions[dim_key][field_key] = {
                "question": question,
                "status": status["status"],
                "confidence": status.get("confidence", 0.5),
                "extracted": status.get("extracted"),
            }

    storage.update_session(session_id, dimensions=dimensions)
    storage.log_audit(
        session_id,
        "draft_map",
        "dimensions_mapped",
        f"Mapped {len(DRAFT_FIELDS)} dims ({'llm' if use_llm else 'heuristic'})",
    )

    session["dimensions"] = dimensions
    esc = should_escalate(session)
    if esc:
        storage.update_session(session_id, tier=esc[0])
        storage.log_audit(session_id, "draft_map", "auto_escalation", esc[1])

    return dimensions


def _screen_dimension_llm(dim_key: str, context: str) -> bool:
    dim_name = DIMENSION_NAMES.get(dim_key, dim_key)
    screen_q = DIMENSION_SCREEN_QUESTIONS.get(dim_key, "")
    if not screen_q:
        return True

    prompt = f"""Given this task context, is the dimension "{dim_name}" applicable?
Screening question: {screen_q}

Context: {context[:800]}"""

    result = _llm_call(prompt, SCREEN_SCHEMA, timeout=15)
    if result is not None:
        return result.get("applicable", True)
    return True


def _assess_field_llm(field_key: str, question: str, context: str) -> dict:
    prompt = f"""Assess whether this DRAFT field is addressed by the context.

Field {field_key}: {question}

Context: {context[:1200]}

Rules:
- SATISFIED: Context clearly addresses this field.
- AMBIGUOUS: Context partially or vaguely addresses it.
- MISSING: Context does not address this field.
- Extract relevant info if SATISFIED or AMBIGUOUS.
- Rate confidence 0.0 to 1.0."""

    result = _llm_call(prompt, FIELD_SCHEMA, timeout=20)
    if result and result.get("status") in ("SATISFIED", "AMBIGUOUS", "MISSING"):
        # Hard enforcement: strip fabricated extractions from non-SATISFIED fields
        if result["status"] in ("AMBIGUOUS", "MISSING"):
            result["extracted"] = ""
        return result
    return _assess_field_embedding(field_key, question, context, [])


def _assess_field_embedding(field_key: str, question: str, context: str, context_emb: list) -> dict:
    if not context_emb:
        context_emb = _embed(context[:1000])
    field_emb = _get_field_embedding(field_key)

    if not context_emb or not field_emb:
        # No embedding available — keyword fallback
        return _assess_field_keyword(field_key, context)

    sim = _cosine_sim(context_emb, field_emb)

    if sim >= 0.55:
        return {"status": "SATISFIED", "confidence": round(sim, 3), "extracted": f"Semantic match ({sim:.3f})"}
    elif sim >= 0.40:
        return {"status": "AMBIGUOUS", "confidence": round(sim, 3), "extracted": f"Partial match ({sim:.3f})"}
    return {"status": "MISSING", "confidence": round(max(0.1, 1.0 - sim), 3)}


def _assess_field_keyword(field_key: str, context: str) -> dict:
    """Pure keyword fallback when no LLM or embedding is available."""
    lower = context.lower()
    keywords = {
        "D1": ["building", "creating", "system", "tool", "service", "product"],
        "D2": ["domain", "area", "scope", "field"],
        "D3": ["without", "fail", "break", "depend", "block", "need"],
        "D4": ["alternative", "replace", "existing", "instead", "workaround"],
        "D5": ["not about", "non-goal", "exclude", "out of scope", "won't"],
        "R1": ["authority", "owner", "decision maker", "approve", "responsible"],
        "R2": ["allowed", "permitted", "can do", "authorized"],
        "R3": ["forbidden", "prohibited", "cannot", "must not", "never"],
        "R4": ["stop", "halt", "abort", "limit", "condition"],
        "R5": ["interface", "api", "connect", "integrate", "interact"],
        "A1": ["input", "accept", "receive", "data", "file"],
        "A2": ["reject", "block", "invalid", "forbidden input"],
        "A3": ["output", "produce", "generate", "return", "response"],
        "A4": ["forbidden output", "must not produce", "never output"],
        "A5": ["example", "correct", "expected"],
        "A6": ["incorrect", "wrong", "bad example"],
        "F1": ["change authority", "modify", "who can change"],
        "F2": ["permitted change", "allowed update", "can modify"],
        "F3": ["frozen", "immutable", "locked", "cannot change"],
        "F4": ["review trigger", "audit", "threshold", "when to review"],
        "T1": ["success", "pass", "works", "complete", "verified"],
        "T2": ["failure", "fail", "error", "broken", "incorrect"],
        "T3": ["review question", "check", "verify", "audit question"],
        "T4": ["evidence", "proof", "test result", "demonstration"],
    }
    field_kws = keywords.get(field_key, [])
    matches = sum(1 for kw in field_kws if kw in lower)
    if matches >= 2:
        return {"status": "SATISFIED", "confidence": 0.6, "extracted": f"Keyword match ({matches} hits)"}
    elif matches == 1:
        return {"status": "AMBIGUOUS", "confidence": 0.4, "extracted": "Partial keyword match"}
    return {"status": "MISSING", "confidence": 0.3}


def _context_suggests_applicable(dim_key: str, context: str) -> bool:
    lower = context.lower()
    if dim_key == "R":
        return any(w in lower for w in ["authority", "decision", "permission", "limit", "allowed", "forbidden"])
    if dim_key == "A":
        return any(w in lower for w in ["file", "output", "input", "document", "data", "artifact", "create"])
    if dim_key == "F":
        return any(w in lower for w in ["change", "update", "evolve", "lifecycle", "adapt", "version"])
    return True


# ── Elicitation ───────────────────────────────────────────


def generate_elicitation(session_id: str) -> list[dict]:
    """Generate targeted questions for MISSING/AMBIGUOUS fields."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return [closed]

    session = storage.get_session(session_id)
    if not session:
        return [{"error": f"Session {session_id} not found"}]

    questions: list[dict[str, Any]] = []
    dims = session.get("dimensions", {})
    intent = session.get("intent", "")
    use_llm = _llm_available()

    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for field_key, info in fields.items():
            if field_key.startswith("_"):
                continue
            status = info.get("status", "MISSING")
            if status in ("MISSING", "AMBIGUOUS"):
                q = DRAFT_FIELDS.get(dim_key, {}).get(field_key, "")
                suggestion = _smart_suggestion(field_key, q, intent) if use_llm else _suggest_answer(field_key, intent)
                questions.append(
                    {
                        "dimension": f"{dim_key} — {DIMENSION_NAMES.get(dim_key, dim_key)}",
                        "field": field_key,
                        "question": q,
                        "current_status": status,
                        "confidence": info.get("confidence", 0.0),
                        "suggestion": suggestion,
                        "extracted": info.get("extracted"),
                    }
                )

    storage.log_audit(session_id, "draft_elicit", "questions_generated", f"Generated {len(questions)} questions")

    # Collaborative framing (PEACE + MI) — added to each question
    for item in questions:
        item["framing"] = _collaborative_frame(item["field"], item.get("current_status", "MISSING"))

    return questions


def _collaborative_frame(field_key: str, status: str) -> str:
    """Generate collaborative framing hint for a question (PEACE + MI)."""
    if status == "AMBIGUOUS":
        return f"I picked up something for {field_key} but need your clarification to get it right."
    return f"I couldn't find {field_key} in what you've shared — your input here will shape the work."


def _smart_suggestion(field_key: str, question: str, intent: str) -> str | None:
    if not intent:
        return _suggest_answer(field_key, intent)

    prompt = f"""Generate a helpful suggestion for this DRAFT elicitation question.

Field: {field_key}
Question: {question}
Task intent: {intent[:300]}

Provide a concrete, actionable suggestion with an example if possible."""

    result = _llm_call(prompt, SUGGESTION_SCHEMA, timeout=15)
    if result and result.get("suggestion"):
        s = result["suggestion"]
        if result.get("example"):
            s += f"\nExample: {result['example']}"
        return s
    return _suggest_answer(field_key, intent)


def _suggest_answer(field_key: str, intent: str) -> str | None:
    scaffolds = {
        "D1": f"Based on '{intent[:80]}...', this creates [specific deliverable].",
        "D3": "If this didn't exist, what downstream work would be blocked?",
        "D5": "Non-goals prevent scope creep: 'This does NOT include [X].'",
        "R1": "Who is the human decision-maker?",
        "R4": "List 3+ stop conditions: 'STOP if scope expands beyond [X].'",
        "A5": "Provide one correct example of expected output.",
        "A6": "Provide one incorrect example showing what to avoid.",
        "T1": "Success = [measurable outcome].",
        "T2": "Failure = [measurable outcome].",
        "T3": "3+ review questions: 'Does the output address [requirement]?'",
    }
    return scaffolds.get(field_key)


# ── Open Elicitation (Cognitive Interview) ────────────────


def open_elicitation(session_id: str) -> dict:
    """Open elicitation step — single unstructured question before mapping.

    For TASK+ tiers, asks the human to describe intent freely before
    the AI interprets. Prevents anchoring bias (GAP-02).
    Based on Cognitive Interview and PEACE model principles.
    """
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    tier = session.get("tier", "TASK")
    ceremony = TIER_CEREMONY.get(tier, "visible")

    # TRIVIAL/LOOKUP skip open elicitation
    if ceremony in ("invisible", "tag"):
        storage.log_audit(session_id, "open_elicit", "skipped", f"Ceremony={ceremony}, tier={tier}")
        return {
            "session_id": session_id,
            "skipped": True,
            "reason": f"Tier {tier} uses {ceremony} ceremony — open elicitation not needed.",
        }

    intent = session.get("intent", "")

    # Generate a contextual open question
    if _llm_available() and intent:
        prompt = f"""Generate one open-ended elicitation question for this task.
The question should invite the human to describe their full intent before any AI interpretation.
Do NOT ask about specific fields. Ask them to paint the picture.

Task intent: {intent[:300]}

Rules:
- One question only
- Open-ended (not yes/no)
- Invites elaboration, not confirmation
- Acknowledges what they've said so far"""

        result = _llm_call(prompt, {"type": "object", "properties": {
            "question": {"type": "string"},
            "framing": {"type": "string"},
        }, "required": ["question"]}, timeout=15)

        if result and result.get("question"):
            q = result["question"]
            framing = result.get(
                "framing", "Your description helps me map this accurately before I start interpreting."
            )
            storage.log_audit(session_id, "open_elicit", "generated", q[:200])
            return {
                "session_id": session_id,
                "question": q,
                "framing": framing,
                "instruction": "Present this question to the human. Their response becomes context for draft_map.",
            }

    # Fallback: static open question
    fallback_q = (
        "Before I map this out — can you describe in your own words "
        "what you're trying to accomplish and what success looks like?"
    )
    storage.log_audit(session_id, "open_elicit", "fallback", f"Tier={tier}")
    return {
        "session_id": session_id,
        "question": fallback_q,
        "framing": "Your description shapes how I understand this — nothing is assumed yet.",
        "instruction": "Present this question to the human. Their response becomes context for draft_map.",
    }


# ── Assumption Quality Scoring ────────────────────────────


_QUALITY_SCHEMA = {
    "type": "object",
    "properties": {
        "falsifiability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "impact": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "novelty": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
    "required": ["falsifiability", "impact", "novelty"],
}


def score_assumptions(session_id: str) -> dict:
    """Score each assumption by falsifiability, impact, and novelty.

    Returns quality scores and flags low-quality assumptions for replacement.
    Based on CIA Key Assumptions Check quality criteria.
    """
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    assumptions = session.get("assumptions", [])
    if not assumptions:
        return {"session_id": session_id, "scored": 0, "results": [], "note": "No assumptions to score."}

    use_llm = _llm_available()
    results = []

    for i, assumption in enumerate(assumptions):
        claim = assumption.get("claim", "")
        if not claim:
            continue

        if use_llm:
            score = _score_assumption_llm(claim, session.get("intent", ""))
        else:
            score = _score_assumption_heuristic(claim, assumption.get("source", ""))

        quality = round((score["falsifiability"] + score["impact"] + score["novelty"]) / 3, 3)
        low_quality = quality < 0.4

        result = {
            "index": i,
            "claim": claim[:100],
            "falsifiability": score["falsifiability"],
            "impact": score["impact"],
            "novelty": score["novelty"],
            "quality_score": quality,
            "low_quality": low_quality,
        }
        if low_quality:
            result["warning"] = "Low quality — consider replacing with a more specific, testable claim."
        results.append(result)

        # Update assumption in session with quality score
        assumptions[i]["quality_score"] = quality
        assumptions[i]["low_quality"] = low_quality

    storage.update_session(session_id, assumptions=assumptions)
    storage.log_audit(
        session_id, "score_assumptions", f"{len(results)} scored",
        f"Low quality: {sum(1 for r in results if r.get('low_quality'))}",
    )

    return {
        "session_id": session_id,
        "scored": len(results),
        "average_quality": round(sum(r["quality_score"] for r in results) / len(results), 3) if results else 0,
        "low_quality_count": sum(1 for r in results if r.get("low_quality")),
        "results": results,
    }


def _score_assumption_llm(claim: str, intent: str) -> dict:
    """Score assumption quality using LLM."""
    prompt = f"""Score this governance assumption on three dimensions (0.0-1.0 each):

Assumption: {claim[:200]}
Task intent: {intent[:200]}

Falsifiability: How testable is this? Can you clearly prove it wrong? (1.0 = highly testable, 0.0 = unfalsifiable)
Impact: If this assumption is wrong, how much rework? (1.0 = total rework, 0.0 = trivial)
Novelty: Is this a genuine risk or just restating the obvious? (1.0 = novel insight, 0.0 = obvious restatement)"""

    result = _llm_call(prompt, _QUALITY_SCHEMA, timeout=15)
    if result:
        return {
            "falsifiability": result.get("falsifiability", 0.5),
            "impact": result.get("impact", 0.5),
            "novelty": result.get("novelty", 0.5),
        }
    return _score_assumption_heuristic(claim, "llm_fallback")


def _score_assumption_heuristic(claim: str, source: str) -> dict:
    """Heuristic assumption quality scoring without LLM."""
    lower = claim.lower()

    # Falsifiability: does it have testable conditions?
    falsifiability = 0.5
    test_words = ["if ", "when ", "unless ", "would ", "could ", "fails", "breaks", "wrong"]
    if any(w in lower for w in test_words):
        falsifiability = 0.7
    if "not " in lower or "never " in lower or "always " in lower:
        falsifiability = 0.8  # Strong claims are more falsifiable

    # Impact: does it reference scope, architecture, or critical systems?
    impact = 0.5
    critical_words = ["architecture", "governance", "security", "scope", "authority", "production", "data"]
    if any(w in lower for w in critical_words):
        impact = 0.7

    # Novelty: is it just echoing a confirmed field?
    novelty = 0.5
    restatement_patterns = ["for d", "for r", "for a", "for f", "for t", "context_extraction"]
    if source == "context_extraction" or any(p in lower for p in restatement_patterns):
        novelty = 0.2  # Likely restating confirmed fields
    if source in ("llm_adversarial", "manual", "devils_advocate"):
        novelty = 0.7

    return {"falsifiability": falsifiability, "impact": impact, "novelty": novelty}


# ── Assumptions ───────────────────────────────────────────

_ASSUMPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "falsifier": {"type": "string"},
        "impact": {"type": "string"},
    },
    "required": ["claim", "falsifier"],
}


def generate_assumptions(session_id: str) -> list[dict]:
    """Surface key assumptions as falsifiable claims.

    When LLM is available, generates adversarial assumptions that test
    genuine risks rather than restating confirmed fields.
    Devil's Advocate intensity scales by tier:
      CASUAL: 1-2 lightweight assumptions
      STANDARD: 2-3 assumptions with light DA
      CONSEQUENTIAL: 3-5 assumptions with full DA
    """
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return [closed]

    session = storage.get_session(session_id)
    if not session:
        return [{"error": f"Session {session_id} not found"}]

    dims = session.get("dimensions", {})
    tier = session.get("tier", "STANDARD")
    use_llm = _llm_available()

    # Determine assumption count by tier
    max_assumptions = TIER_ASSUMPTIONS.get(tier, 3)

    if use_llm:
        assumptions = _generate_llm_assumptions(dims, session.get("intent", ""), tier, max_assumptions)
    else:
        assumptions = _generate_heuristic_assumptions(dims, max_assumptions)

    storage.update_session(session_id, assumptions=assumptions)
    storage.log_audit(
        session_id,
        "draft_assumptions",
        "generated",
        f"{len(assumptions)} assumptions (tier={tier}, {'llm' if use_llm else 'heuristic'})",
    )
    return assumptions


def _generate_llm_assumptions(dims: dict, intent: str, tier: str, max_count: int) -> list[dict]:
    """Generate adversarial assumptions using LLM."""
    # Collect confirmed field summaries for context
    field_summary = []
    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            field_summary.append(f"{dim_key}: screened as N/A")
            continue
        for fk, info in fields.items():
            if fk.startswith("_") or not isinstance(info, dict):
                continue
            status = info.get("status", "MISSING")
            extracted = info.get("extracted", "")
            if status == "CONFIRMED" and extracted:
                field_summary.append(f"{fk}: {extracted[:100]}")

    da_instruction = ""
    if tier == "CONSEQUENTIAL":
        da_instruction = (
            "\nDevil's Advocate: For each assumption, briefly argue WHY it might be wrong. "
            "Push back on the most confident claims."
        )
    elif tier == "STANDARD":
        da_instruction = "\nInclude at least one assumption that challenges the scope or success criteria."

    prompt = f"""Generate {max_count} falsifiable assumptions for this DRAFT session.

Intent: {intent[:300]}

Confirmed fields:
{chr(10).join(field_summary[:15])}

Rules:
- Each assumption must be a specific, testable claim (not a restatement of confirmed fields).
- Each must have a clear falsifier: what evidence would prove it wrong?
- Focus on GENUINE RISKS: wrong scope, missing dependencies, unstated constraints, incorrect success criteria.
- Do NOT just restate what was confirmed. Challenge it.{da_instruction}"""

    assumptions = []
    for _i in range(max_count):
        result = _llm_call(prompt, _ASSUMPTION_SCHEMA, timeout=20)
        if result and result.get("claim"):
            assumptions.append({
                "claim": result["claim"],
                "source": "llm_adversarial",
                "falsifier": result.get("falsifier", f"If '{result['claim'][:80]}' is wrong, re-elicit."),
                "impact": result.get("impact", ""),
            })
        if len(assumptions) >= max_count:
            break

    # If LLM didn't produce enough, supplement with heuristic
    if len(assumptions) < max_count:
        heuristic = _generate_heuristic_assumptions(dims, max_count - len(assumptions))
        assumptions.extend(heuristic)

    return assumptions[:max_count]


def _generate_heuristic_assumptions(dims: dict, max_count: int) -> list[dict]:
    """Generate assumptions from field extractions (fallback)."""
    assumptions = []

    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            assumptions.append({
                "claim": f"Dimension {dim_key} ({DIMENSION_NAMES.get(dim_key, '')}) is not applicable.",
                "source": "screening",
                "falsifier": (
                    f"If this task involves {DIMENSION_NAMES.get(dim_key, '').lower()}, screening was wrong."
                ),
            })
            continue
        for field_key, info in fields.items():
            if field_key.startswith("_"):
                continue
            if info.get("status") == "SATISFIED" and info.get("extracted"):
                assumptions.append({
                    "claim": f"For {field_key}: {info['extracted']}",
                    "source": "context_extraction",
                    "confidence": info.get("confidence", 0.5),
                    "falsifier": f"If wrong, re-elicit {field_key}.",
                })

    return assumptions[:max_count]


# ── Gate ──────────────────────────────────────────────────

_PERFUNCTORY_PATTERNS = {"yes", "agreed", "as stated", "correct", "confirmed", "ok", "okay", "sure", "yep", "ack"}


def _detect_perfunctory(dims: dict) -> list[str]:
    """Detect perfunctory confirmation patterns (DFT-08).

    Flags but doesn't block — adds warnings to gate results.
    """
    warnings = []
    values = []

    for _dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for fk, info in fields.items():
            if fk.startswith("_") or not isinstance(info, dict):
                continue
            if info.get("status") == "CONFIRMED":
                val = str(info.get("extracted", "")).strip().lower()
                values.append((fk, val))

    # Check for repeated identical values across fields
    value_counts: dict[str, list[str]] = {}
    for fk, val in values:
        value_counts.setdefault(val, []).append(fk)
    for val, fks in value_counts.items():
        if len(fks) > 1 and val:
            warnings.append(f"Repeated value '{val[:30]}' across fields: {', '.join(fks)}")

    # Check for known perfunctory patterns
    for fk, val in values:
        if val in _PERFUNCTORY_PATTERNS:
            warnings.append(f"{fk}: perfunctory confirmation ('{val}')")

    return warnings


def check_gate(session_id: str) -> dict:
    """Check whether all applicable fields are confirmed."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return {"passed": False, "blockers": [closed["error"]], "summary": "ERROR"}

    session = storage.get_session(session_id)
    if not session:
        return {"passed": False, "blockers": ["Session not found"], "summary": "ERROR"}

    dims = session.get("dimensions", {})
    blockers = []
    confirmed = 0
    total = 0

    if not dims:
        blockers.append("No dimensions mapped — call draft_map before checking gate")

    for _dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for field_key, info in fields.items():
            if field_key.startswith("_"):
                continue
            total += 1
            status = info.get("status", "MISSING")
            if status == "CONFIRMED":
                extracted = info.get("extracted", "")
                if not extracted or not str(extracted).strip() or len(str(extracted).strip()) < 3:
                    blockers.append(f"{field_key}: CONFIRMED but empty/insufficient content (possible bypass)")
                    storage.log_audit(
                        session_id,
                        "draft_gate",
                        "empty_confirm_detected",
                        f"{field_key} confirmed with empty/short content",
                    )
                else:
                    confirmed += 1
            elif status in ("MISSING", "AMBIGUOUS"):
                blockers.append(f"{field_key}: {status}")

    assumptions = session.get("assumptions", [])
    unverified = [a for a in assumptions if not a.get("verified")]
    if unverified:
        blockers.append(f"{len(unverified)} unverified assumption(s)")

    # Perfunctory confirmation detection (DFT-08) — warn, don't block
    perfunctory_warnings = _detect_perfunctory(dims)

    passed = len(blockers) == 0
    if passed:
        storage.update_session(session_id, gate_passed=1)

    storage.log_audit(session_id, "draft_gate", "gate_check", f"{'PASS' if passed else 'FAIL'}: {confirmed}/{total}")

    result = {
        "passed": passed,
        "confirmed": confirmed,
        "total": total,
        "blockers": blockers,
        "summary": f"{'[PASS]' if passed else '[BLOCKED]'}: {confirmed}/{total}",
    }

    if perfunctory_warnings:
        result["warnings"] = perfunctory_warnings

    # Extension point: post-gate hook (e.g., cross-gate wiring)
    if passed:
        hook = get_post_gate_hook()
        if hook is not None:
            with contextlib.suppress(Exception):
                hook(session_id, result)  # Post-gate hooks are advisory, not blocking

    # M1.5: Context enrichment — compliant agents get rich context for free
    if passed:
        enrichment = {}
        for dim_key in ["D", "R", "A", "F", "T"]:
            dim_fields = dims.get(dim_key, {})
            if isinstance(dim_fields, dict) and dim_fields.get("_screened"):
                enrichment[dim_key] = {"_screened": True, "_reason": dim_fields.get("_reason", "N/A")}
                continue
            dim_data = {}
            for fk, info in dim_fields.items():
                if fk.startswith("_") or not isinstance(info, dict):
                    continue
                dim_data[fk] = {
                    "value": info.get("extracted", ""),
                    "question": info.get("question", ""),
                    "status": info.get("status", "UNKNOWN"),
                }
            enrichment[dim_key] = dim_data
        result["context_enrichment"] = enrichment
        result["tier"] = session.get("tier", "UNKNOWN")

    return result


# ── Field Operations ──────────────────────────────────────


def confirm_field(session_id: str, field_key: str, value: str) -> dict:
    """Confirm a DRAFT field with a human-provided answer."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    if not value or not value.strip():
        storage.log_audit(session_id, "confirm_field", f"{field_key} REJECTED", "Empty or whitespace-only value")
        return {"error": f"Cannot confirm {field_key} with empty value.", "field": field_key, "status": "REJECTED"}

    stripped = value.strip()
    if len(stripped) < 3:
        storage.log_audit(
            session_id,
            "confirm_field",
            f"{field_key} REJECTED",
            f"Value too short ({len(stripped)} chars): '{stripped}'",
        )
        return {
            "error": f"Cannot confirm {field_key} with '{stripped}'. Provide a substantive answer (3+ characters).",
            "field": field_key,
            "status": "REJECTED",
        }

    dims = session.get("dimensions", {})
    dim_key = field_key[0]
    if dim_key not in dims:
        return {"error": f"Dimension {dim_key} not mapped"}
    if isinstance(dims[dim_key], dict) and dims[dim_key].get("_screened"):
        return {"error": f"Dimension {dim_key} screened. Unscreen first."}

    dims[dim_key][field_key] = {
        "question": DRAFT_FIELDS.get(dim_key, {}).get(field_key, ""),
        "status": "CONFIRMED",
        "extracted": stripped,
        "confidence": 1.0,
        "confirmed_by": "human",
    }
    storage.update_session(session_id, dimensions=dims)
    storage.log_audit(session_id, "confirm_field", f"{field_key} confirmed", stripped[:200])
    return {"field": field_key, "status": "CONFIRMED", "value": stripped}


def unscreen_dimension(session_id: str, dimension_key: str) -> dict:
    """Reverse screening on a dimension incorrectly marked N/A."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    dim_key = dimension_key.upper()
    if dim_key in MANDATORY_DIMENSIONS:
        return {"error": f"{dim_key} is mandatory."}

    dims = session.get("dimensions", {})
    if dim_key not in dims:
        return {"error": f"{dim_key} not in session."}
    if not (isinstance(dims[dim_key], dict) and dims[dim_key].get("_screened")):
        return {"error": f"{dim_key} not screened."}

    fields = DRAFT_FIELDS.get(dim_key, {})
    dims[dim_key] = {
        fk: {"question": q, "status": "MISSING", "confidence": 0.0, "extracted": None} for fk, q in fields.items()
    }

    storage.update_session(session_id, dimensions=dims)
    storage.log_audit(session_id, "unscreen", f"{dim_key} unscreened", f"{len(fields)} fields MISSING")
    return {"unscreened": dim_key, "fields_added": list(fields.keys())}


def add_assumption(session_id: str, claim: str, source: str = "manual", falsifier: str = "") -> dict:
    """Add a manually authored assumption."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    if not claim or not claim.strip():
        return {"error": "Claim cannot be empty."}

    assumptions = session.get("assumptions", [])
    new = {
        "claim": claim.strip(),
        "source": source or "manual",
        "falsifier": falsifier.strip() if falsifier else f"If '{claim.strip()[:80]}' is wrong, re-elicit.",
    }
    assumptions.append(new)
    storage.update_session(session_id, assumptions=assumptions)
    idx = len(assumptions) - 1
    storage.log_audit(session_id, "add_assumption", f"[{idx}] added", claim[:200])
    return {"index": idx, "assumption": new}


def override_gate(session_id: str, reason: str) -> dict:
    """Override a blocked gate with logged reason (authorized override)."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    if not reason or not reason.strip():
        return {"error": "Reason mandatory."}

    gate = check_gate(session_id)
    if gate.get("passed"):
        return {"note": "Already passed.", "gate": gate}

    storage.update_session(session_id, gate_passed=1)
    storage.log_audit(
        session_id, "override_gate", "OVERRIDDEN", f"AUTHORIZED: {reason.strip()}. Blockers: {gate.get('blockers', [])}"
    )
    return {"status": "OVERRIDDEN", "reason": reason.strip(), "blockers": gate.get("blockers", [])}


def verify_assumption(session_id: str, index: int, verified: bool, note: str = "") -> dict:
    """Verify or reject an assumption."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    assumptions = session.get("assumptions", [])
    if index < 0 or index >= len(assumptions):
        return {"error": f"Index {index} out of range"}

    assumptions[index]["verified"] = verified
    assumptions[index]["note"] = note
    storage.update_session(session_id, assumptions=assumptions)
    action = "verified" if verified else "REJECTED"
    storage.log_audit(session_id, "verify_assumption", f"[{index}] {action}", note)

    if not verified:
        return {"result": action, "action_needed": "Re-elicit affected fields."}
    return {"result": action}


# ── Batch Operations ──────────────────────────────────────


def confirm_batch(session_id: str, fields: dict) -> dict:
    """Confirm multiple DRAFT fields in a single call.

    Args:
        session_id: Active session ID.
        fields: Dict of {field_key: value} pairs to confirm.

    Returns dict with confirmed/rejected/errors counts and per-field results.
    """
    closed = _check_open(session_id)
    if closed:
        return closed
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    if not fields or not isinstance(fields, dict):
        return {"error": "fields must be a non-empty dict of {field_key: value} pairs"}

    results = {}
    confirmed = 0
    rejected = 0
    errors = 0

    dims = session.get("dimensions", {})

    for field_key, value in fields.items():
        fk = str(field_key).strip().upper()

        # Validate value
        if not value or not str(value).strip():
            results[fk] = {"status": "REJECTED", "reason": "Empty value"}
            storage.log_audit(session_id, "confirm_batch", f"{fk} REJECTED", "Empty value")
            rejected += 1
            continue

        stripped = str(value).strip()
        if len(stripped) < 3:
            results[fk] = {"status": "REJECTED", "reason": f"Too short ({len(stripped)} chars)"}
            storage.log_audit(session_id, "confirm_batch", f"{fk} REJECTED", f"Too short: '{stripped}'")
            rejected += 1
            continue

        # Validate dimension exists and not screened
        dim_key = fk[0]
        if dim_key not in dims:
            results[fk] = {"status": "ERROR", "reason": f"Dimension {dim_key} not mapped"}
            errors += 1
            continue
        if isinstance(dims[dim_key], dict) and dims[dim_key].get("_screened"):
            results[fk] = {"status": "ERROR", "reason": f"Dimension {dim_key} screened"}
            errors += 1
            continue

        # Confirm the field
        dims[dim_key][fk] = {
            "question": DRAFT_FIELDS.get(dim_key, {}).get(fk, ""),
            "status": "CONFIRMED",
            "extracted": stripped,
            "confidence": 1.0,
            "confirmed_by": "human",
        }
        results[fk] = {"status": "CONFIRMED", "value": stripped}
        confirmed += 1

    # Single DB write for all changes
    storage.update_session(session_id, dimensions=dims)
    storage.log_audit(
        session_id,
        "confirm_batch",
        f"{confirmed} confirmed, {rejected} rejected, {errors} errors",
        f"Fields: {list(fields.keys())}",
    )

    return {
        "session_id": session_id,
        "confirmed": confirmed,
        "rejected": rejected,
        "errors": errors,
        "total": len(fields),
        "results": results,
    }


def quick_confirm_satisfied(session_id: str) -> dict:
    """Confirm all SATISFIED (pre-extracted) fields in one call.

    Promotes SATISFIED fields with substantive extracted content to CONFIRMED.
    MISSING/AMBIGUOUS fields are untouched.
    """
    closed = _check_open(session_id)
    if closed:
        return closed
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    dims = session.get("dimensions", {})
    promoted = []

    for _dim_key, dim_fields in dims.items():
        if not isinstance(dim_fields, dict) or dim_fields.get("_screened"):
            continue
        for fk, info in dim_fields.items():
            if fk.startswith("_") or not isinstance(info, dict):
                continue
            if info.get("status") == "SATISFIED" and info.get("extracted") and len(str(info["extracted"]).strip()) >= 3:
                info["status"] = "CONFIRMED"
                info["confirmed_by"] = "human_quick_confirm"
                promoted.append(fk)

    if promoted:
        storage.update_session(session_id, dimensions=dims)
        storage.log_audit(session_id, "quick_confirm", f"{len(promoted)} fields promoted", f"Fields: {promoted}")

    return {
        "session_id": session_id,
        "promoted_count": len(promoted),
        "promoted_fields": promoted,
        "note": (
            "SATISFIED fields promoted to CONFIRMED. MISSING/AMBIGUOUS still need individual confirmation."
            if promoted
            else "No SATISFIED fields to promote. Use confirm_field or confirm_batch for remaining fields."
        ),
    }


def verify_batch(session_id: str, verifications: dict) -> dict:
    """Verify multiple assumptions in a single call.

    Args:
        session_id: Active session ID.
        verifications: Dict of {index: bool} pairs.

    Returns dict with verified/rejected counts and per-assumption results.
    """
    closed = _check_open(session_id)
    if closed:
        return closed
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    if not verifications or not isinstance(verifications, dict):
        return {"error": "verifications must be a non-empty dict of {index: bool} pairs"}

    assumptions = session.get("assumptions", [])
    results = {}
    verified_count = 0
    rejected_count = 0

    for idx_str, verified in verifications.items():
        idx = int(idx_str)
        if idx < 0 or idx >= len(assumptions):
            results[str(idx)] = {"status": "ERROR", "reason": f"Index {idx} out of range (0-{len(assumptions) - 1})"}
            continue

        assumptions[idx]["verified"] = bool(verified)
        if verified:
            results[str(idx)] = {"status": "VERIFIED", "claim": assumptions[idx].get("claim", "")[:100]}
            verified_count += 1
        else:
            results[str(idx)] = {"status": "REJECTED", "claim": assumptions[idx].get("claim", "")[:100]}
            rejected_count += 1

    storage.update_session(session_id, assumptions=assumptions)
    storage.log_audit(
        session_id,
        "verify_batch",
        f"{verified_count} verified, {rejected_count} rejected",
        f"Indices: {list(verifications.keys())}",
    )

    return {
        "session_id": session_id,
        "verified": verified_count,
        "rejected": rejected_count,
        "total": len(verifications),
        "results": results,
        "note": "Rejected assumptions may require re-elicitation of affected fields." if rejected_count else "",
    }


def elicitation_review(session_id: str) -> dict:
    """Self-assessment of elicitation quality."""
    # M1.3: Closed session guard
    closed = _check_open(session_id)
    if closed:
        return closed

    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    dims = session.get("dimensions", {})
    findings = []

    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        gaps = sum(
            1
            for k, v in fields.items()
            if not k.startswith("_") and isinstance(v, dict) and v.get("status") in ("MISSING", "AMBIGUOUS")
        )
        if gaps > 2:
            findings.append(f"{dim_key}: {gaps} gaps")

    low_conf = []
    for _dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for k, v in fields.items():
            if k.startswith("_") or not isinstance(v, dict):
                continue
            if v.get("status") == "CONFIRMED" and v.get("confidence", 1.0) < 0.6:
                low_conf.append(f"{k}={v.get('confidence', 0):.2f}")

    if low_conf:
        findings.append(f"Low-confidence: {', '.join(low_conf)}")

    assumptions = session.get("assumptions", [])
    unv = sum(1 for a in assumptions if not a.get("verified"))
    if unv:
        findings.append(f"{unv} unverified assumptions")

    quality = "HIGH" if not findings else "NEEDS_ATTENTION"
    storage.log_audit(session_id, "review", f"quality={quality}", "; ".join(findings) or "Clean")

    features = ["keyword_classification", "dimension_screening", "confidence_scoring"]
    if _llm_available():
        features.extend(["llm_classification", "smart_suggestions"])
    if _embed_available():
        features.append("embedding_assessment")

    # Session analytics (FLOW-1.0)
    analytics = _session_analytics(session)

    return {"quality": quality, "findings": findings, "features": features, "analytics": analytics}


def _session_analytics(session: dict) -> dict:
    """Compute session-level metrics for quality review."""
    dims = session.get("dimensions", {})
    assumptions = session.get("assumptions", [])

    # Confidence distribution
    confidences = []
    confirmed_count = 0
    total_fields = 0
    for _dk, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for fk, info in fields.items():
            if fk.startswith("_") or not isinstance(info, dict):
                continue
            total_fields += 1
            conf = info.get("confidence", 0.0)
            confidences.append(conf)
            if info.get("status") == "CONFIRMED":
                confirmed_count += 1

    # Assumption rejection rate
    total_assumptions = len(assumptions)
    rejected_assumptions = sum(1 for a in assumptions if a.get("verified") is False)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    low_confidence_count = sum(1 for c in confidences if c < 0.5)

    return {
        "total_fields": total_fields,
        "confirmed_fields": confirmed_count,
        "average_confidence": round(avg_confidence, 3),
        "low_confidence_fields": low_confidence_count,
        "assumption_count": total_assumptions,
        "assumption_rejection_rate": round(rejected_assumptions / total_assumptions, 2) if total_assumptions else 0.0,
        "tier": session.get("tier", "UNKNOWN"),
    }

_TIER_ORDER = ["TRIVIAL", "LOOKUP", "TASK", "MULTI", "CONSEQUENTIAL"]


def escalate_tier(session_id: str, reason: str) -> dict:
    """Manually escalate session tier. Casual → Standard → Consequential."""
    closed = _check_open(session_id)
    if closed:
        return closed
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    if not reason or not reason.strip():
        return {"error": "Reason mandatory."}

    current_tier = session["tier"]
    # Normalize legacy tier names
    if current_tier in LEGACY_MAP:
        current_tier = LEGACY_MAP[current_tier]
    current_idx = _TIER_ORDER.index(current_tier) if current_tier in _TIER_ORDER else 0
    if current_idx >= len(_TIER_ORDER) - 1:
        return {"tier": "CONSEQUENTIAL", "note": "Already at maximum tier."}

    new_tier = _TIER_ORDER[current_idx + 1]
    storage.update_session(session_id, tier=new_tier)
    storage.log_audit(session_id, "escalate", f"{session['tier']} -> {new_tier}", reason)
    return {"previous_tier": session["tier"], "new_tier": new_tier, "reason": reason}


def deescalate_tier(session_id: str, reason: str) -> dict:
    """Manually de-escalate session tier (authorized override). Logged but honored."""
    closed = _check_open(session_id)
    if closed:
        return closed
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    if not reason or not reason.strip():
        return {"error": "Reason mandatory."}

    current_tier = session["tier"]
    # Normalize legacy tier names
    if current_tier in LEGACY_MAP:
        current_tier = LEGACY_MAP[current_tier]
    current_idx = _TIER_ORDER.index(current_tier) if current_tier in _TIER_ORDER else len(_TIER_ORDER) - 1
    if current_idx <= 0:
        return {"tier": "TRIVIAL", "note": "Already at minimum tier."}

    new_tier = _TIER_ORDER[current_idx - 1]
    storage.update_session(session_id, tier=new_tier)
    storage.log_audit(session_id, "deescalate", f"{session['tier']} -> {new_tier}", f"AUTHORIZED: {reason}")
    return {
        "previous_tier": session["tier"],
        "new_tier": new_tier,
        "reason": reason,
        "note": "De-escalation honored and logged. DRAFT mapping still occurs internally.",
    }
