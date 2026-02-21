"""DRAFT Protocol Engine — Intake Governance Intelligence.

Features:
  1. Tier classification — keyword fast-path + optional LLM semantic classification
  2. Field assessment — optional embedding-based cosine similarity or keyword heuristics
  3. Context-aware suggestions — optional LLM scaffolds or static templates
  4. Classification confidence scoring — 0.0-1.0 on all assessments
  5. Graceful degradation — works without any LLM, better with one

Supports any LLM provider via DRAFT_LLM_PROVIDER env var:
  ollama, openai (+ compatible APIs), anthropic, or none (keyword-only).
"""
import math

from draft_protocol import providers, storage
from draft_protocol.config import (
    CONSEQUENTIAL_TRIGGERS,
    DIMENSION_NAMES,
    DIMENSION_SCREEN_QUESTIONS,
    DRAFT_FIELDS,
    MANDATORY_DIMENSIONS,
    STANDARD_TRIGGERS,
)

# ── LLM Schemas ───────────────────────────────────────────

TIER_SCHEMA = {
    "type": "object",
    "properties": {
        "tier": {"type": "string", "enum": ["CASUAL", "STANDARD", "CONSEQUENTIAL"]},
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
    return dot / (na * nb)


def _llm_call(prompt: str, schema: dict, timeout: int = 30) -> dict | None:
    """Structured LLM call via configured provider. Returns parsed dict or None."""
    return providers.chat(prompt, schema, timeout)


# ── Tier Classification ───────────────────────────────────

def classify_tier(message: str) -> tuple[str, str, float]:
    """Classify message into CASUAL / STANDARD / CONSEQUENTIAL.

    Returns (tier, reasoning, confidence).
    Uses keyword fast-path first, then LLM if available and message is ambiguous.
    """
    message = str(message).strip() if message is not None else ""
    if not message:
        return "REJECTED", "Empty or whitespace-only message — cannot classify", 0.0

    lower = message.lower()

    # Fast path: keyword check for consequential
    matched = [t for t in CONSEQUENTIAL_TRIGGERS if t in lower]
    if matched:
        return "CONSEQUENTIAL", f"Keyword match: {', '.join(matched[:3])}", 0.95

    # Fast path: keyword check for standard
    matched = [t for t in STANDARD_TRIGGERS if t in lower]
    if matched:
        return "STANDARD", f"Keyword match: {', '.join(matched[:3])}", 0.85

    # LLM semantic classification for ambiguous messages
    if _llm_available() and len(message.split()) > 3:
        prompt = f"""Classify this user message for an AI governance system.

CASUAL = simple questions, greetings, chat, quick lookups
STANDARD = building, creating, implementing, designing, analyzing, modifying code/files/configs
CONSEQUENTIAL = governance changes, architecture decisions, production deployments, security modifications

Message: {message[:500]}"""

        result = _llm_call(prompt, TIER_SCHEMA, timeout=20)
        if result and result.get("tier") in ("CASUAL", "STANDARD", "CONSEQUENTIAL"):
            return result["tier"], result.get("reasoning", "LLM classification"), result.get("confidence", 0.7)

    # Fallback: length heuristic
    words = len(message.split())
    if words > 50:
        return "STANDARD", f"Length heuristic ({words} words)", 0.5
    return "CASUAL", "No escalation triggers, short message", 0.6


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

    if ambiguous_count > 2 and session["tier"] == "CASUAL":
        return "STANDARD", f"Multiple ambiguous fields ({ambiguous_count})"
    if ambiguous_count > 4 and session["tier"] == "STANDARD":
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
    session = storage.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if not context or not context.strip():
        storage.log_audit(session_id, "draft_map", "REJECTED",
                          "Empty or whitespace-only context")
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
            if (field_key in dimensions[dim_key]
                    and dimensions[dim_key][field_key].get("status") == "CONFIRMED"):
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
    storage.log_audit(session_id, "draft_map", "dimensions_mapped",
                      f"Mapped {len(DRAFT_FIELDS)} dims ({'llm' if use_llm else 'heuristic'})")

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
        return result
    return _assess_field_embedding(field_key, question, context, [])


def _assess_field_embedding(field_key: str, question: str, context: str,
                            context_emb: list) -> dict:
    if not context_emb:
        context_emb = _embed(context[:1000])
    field_emb = _get_field_embedding(field_key)

    if not context_emb or not field_emb:
        # No embedding available — keyword fallback
        return _assess_field_keyword(field_key, context)

    sim = _cosine_sim(context_emb, field_emb)

    if sim >= 0.55:
        return {"status": "SATISFIED", "confidence": round(sim, 3),
                "extracted": f"Semantic match ({sim:.3f})"}
    elif sim >= 0.40:
        return {"status": "AMBIGUOUS", "confidence": round(sim, 3),
                "extracted": f"Partial match ({sim:.3f})"}
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
    session = storage.get_session(session_id)
    if not session:
        return [{"error": f"Session {session_id} not found"}]

    questions = []
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
                suggestion = (
                    _smart_suggestion(field_key, q, intent) if use_llm
                    else _suggest_answer(field_key, intent)
                )
                questions.append({
                    "dimension": f"{dim_key} — {DIMENSION_NAMES.get(dim_key, dim_key)}",
                    "field": field_key,
                    "question": q,
                    "current_status": status,
                    "confidence": info.get("confidence", 0.0),
                    "suggestion": suggestion,
                    "extracted": info.get("extracted"),
                })

    storage.log_audit(session_id, "draft_elicit", "questions_generated",
                      f"Generated {len(questions)} questions")
    return questions


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


# ── Assumptions ───────────────────────────────────────────

def generate_assumptions(session_id: str) -> list[dict]:
    """Surface key assumptions as falsifiable claims."""
    session = storage.get_session(session_id)
    if not session:
        return [{"error": f"Session {session_id} not found"}]

    dims = session.get("dimensions", {})
    assumptions = []

    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            assumptions.append({
                "claim": f"Dimension {dim_key} ({DIMENSION_NAMES.get(dim_key, '')}) is not applicable.",
                "source": "screening",
                "falsifier": f"If this task involves {DIMENSION_NAMES.get(dim_key, '').lower()}, screening was wrong.",
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

    assumptions = assumptions[:5]
    storage.update_session(session_id, assumptions=assumptions)
    storage.log_audit(session_id, "draft_assumptions", "generated",
                      f"{len(assumptions)} assumptions")
    return assumptions


# ── Gate ──────────────────────────────────────────────────

def check_gate(session_id: str) -> dict:
    """Check whether all applicable fields are confirmed."""
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
                    storage.log_audit(session_id, "draft_gate", "empty_confirm_detected",
                                      f"{field_key} confirmed with empty/short content")
                else:
                    confirmed += 1
            elif status in ("MISSING", "AMBIGUOUS"):
                blockers.append(f"{field_key}: {status}")

    assumptions = session.get("assumptions", [])
    unverified = [a for a in assumptions if not a.get("verified")]
    if unverified:
        blockers.append(f"{len(unverified)} unverified assumption(s)")

    passed = len(blockers) == 0
    if passed:
        storage.update_session(session_id, gate_passed=1)

    storage.log_audit(session_id, "draft_gate", "gate_check",
                      f"{'PASS' if passed else 'FAIL'}: {confirmed}/{total}")

    return {
        "passed": passed, "confirmed": confirmed, "total": total,
        "blockers": blockers,
        "summary": f"{'[PASS]' if passed else '[BLOCKED]'}: {confirmed}/{total}",
    }


# ── Field Operations ──────────────────────────────────────

def confirm_field(session_id: str, field_key: str, value: str) -> dict:
    """Confirm a DRAFT field with a human-provided answer."""
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    if not value or not value.strip():
        storage.log_audit(session_id, "confirm_field", f"{field_key} REJECTED",
                          "Empty or whitespace-only value")
        return {"error": f"Cannot confirm {field_key} with empty value.",
                "field": field_key, "status": "REJECTED"}

    stripped = value.strip()
    if len(stripped) < 3:
        storage.log_audit(session_id, "confirm_field", f"{field_key} REJECTED",
                          f"Value too short ({len(stripped)} chars): '{stripped}'")
        return {"error": f"Cannot confirm {field_key} with '{stripped}'. Provide a substantive answer (3+ characters).",
                "field": field_key, "status": "REJECTED"}

    dims = session.get("dimensions", {})
    dim_key = field_key[0]
    if dim_key not in dims:
        return {"error": f"Dimension {dim_key} not mapped"}
    if isinstance(dims[dim_key], dict) and dims[dim_key].get("_screened"):
        return {"error": f"Dimension {dim_key} screened. Unscreen first."}

    dims[dim_key][field_key] = {
        "question": DRAFT_FIELDS.get(dim_key, {}).get(field_key, ""),
        "status": "CONFIRMED", "extracted": stripped,
        "confidence": 1.0, "confirmed_by": "human",
    }
    storage.update_session(session_id, dimensions=dims)
    storage.log_audit(session_id, "confirm_field", f"{field_key} confirmed", stripped[:200])
    return {"field": field_key, "status": "CONFIRMED", "value": stripped}


def unscreen_dimension(session_id: str, dimension_key: str) -> dict:
    """Reverse screening on a dimension incorrectly marked N/A."""
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
        fk: {"question": q, "status": "MISSING", "confidence": 0.0, "extracted": None}
        for fk, q in fields.items()
    }

    storage.update_session(session_id, dimensions=dims)
    storage.log_audit(session_id, "unscreen", f"{dim_key} unscreened", f"{len(fields)} fields MISSING")
    return {"unscreened": dim_key, "fields_added": list(fields.keys())}


def add_assumption(session_id: str, claim: str, source: str = "manual", falsifier: str = "") -> dict:
    """Add a manually authored assumption."""
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
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    if not reason or not reason.strip():
        return {"error": "Reason mandatory."}

    gate = check_gate(session_id)
    if gate.get("passed"):
        return {"note": "Already passed.", "gate": gate}

    storage.update_session(session_id, gate_passed=1)
    storage.log_audit(session_id, "override_gate", "OVERRIDDEN",
                      f"AUTHORIZED: {reason.strip()}. Blockers: {gate.get('blockers', [])}")
    return {"status": "OVERRIDDEN", "reason": reason.strip(), "blockers": gate.get("blockers", [])}


def verify_assumption(session_id: str, index: int, verified: bool, note: str = "") -> dict:
    """Verify or reject an assumption."""
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


def elicitation_review(session_id: str) -> dict:
    """Self-assessment of elicitation quality."""
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    dims = session.get("dimensions", {})
    findings = []

    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        gaps = sum(
            1 for k, v in fields.items()
            if not k.startswith("_") and isinstance(v, dict)
            and v.get("status") in ("MISSING", "AMBIGUOUS")
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

    return {"quality": quality, "findings": findings, "features": features}
