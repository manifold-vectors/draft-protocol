"""DRAFT Protocol MCP Server — Tools for Intake Governance.

Ensures AI understands human intent before execution begins.
Transport: stdio (MCP standard)

Tools (15):
  draft_intake / draft_map / draft_elicit / draft_confirm
  draft_assumptions / draft_verify / draft_gate / draft_review
  draft_status / draft_unscreen / draft_add_assumption
  draft_override / draft_close / draft_escalate / draft_deescalate
"""

from fastmcp import FastMCP

from draft_protocol import engine, storage
from draft_protocol.config import DIMENSION_NAMES

mcp = FastMCP(
    name="DRAFT Protocol Server",
    instructions=(
        "DRAFT (Define, Rules, Artifacts, Flex, Test) ensures AI understands intent "
        "before executing. Use draft_intake to start, draft_map to analyze, "
        "draft_elicit for gaps, draft_confirm for answers, draft_gate to check readiness. "
        "Never skip the gate — no execution on MISSING fields. "
        "Use draft_unscreen to reverse incorrect dimension screening, "
        "draft_add_assumption for manual assumptions, "
        "draft_override for authorized gate bypass on known tool bugs (not governance bypass)."
    ),
    version="0.1.0",
)

# ── Annotation constants ──
_RO = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False}
_CREATE = {"readOnlyHint": False, "idempotentHint": False, "openWorldHint": False}
_DESTRUCT = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@mcp.tool(annotations={"title": "Start DRAFT Session", **_CREATE})
def draft_intake(message: str, tier_override: str = "") -> dict:
    """Start a DRAFT elicitation session.

    Classifies the message into CASUAL / STANDARD / CONSEQUENTIAL
    and creates a tracked session. Use tier_override to force a tier.

    Args:
        message: The user's original request or intent description.
        tier_override: Optional. Force "CASUAL", "STANDARD", or "CONSEQUENTIAL".
    """
    active = storage.get_active_session()
    if active:
        storage.close_session(active["id"])

    if tier_override and tier_override.upper() in ("CASUAL", "STANDARD", "CONSEQUENTIAL"):
        tier = tier_override.upper()
        reasoning = f"Tier manually set to {tier}"
        confidence = 1.0
    else:
        tier, reasoning, confidence = engine.classify_tier(message)

    if tier == "REJECTED":
        return {
            "error": "Cannot create session — message is empty or invalid.",
            "detail": reasoning,
        }

    session_id = storage.create_session(tier, message)
    storage.log_audit(session_id, "draft_intake", "session_created",
                      f"Tier: {tier} (conf: {confidence:.2f}). {reasoning}")

    result = {
        "session_id": session_id,
        "tier": tier,
        "classification_reasoning": reasoning,
        "classification_confidence": confidence,
        "next_step": _next_step_for_tier(tier),
    }

    if tier == "CASUAL":
        result["note"] = "Casual tier: DRAFT mapping is internal only. Respond naturally."

    return result


@mcp.tool(annotations={"title": "Map DRAFT Dimensions", **_WRITE})
def draft_map(session_id: str, context: str) -> dict:
    """Map all 5 DRAFT dimensions against the provided context.

    Screens non-mandatory dimensions (R, A, F) for applicability.
    Labels each field: SATISFIED / AMBIGUOUS / MISSING / N/A.

    Args:
        session_id: Active session ID from draft_intake.
        context: Combined user intent + any clarifications so far.
    """
    dimensions = engine.map_dimensions(session_id, context)
    session = storage.get_session(session_id)

    summary = _dimension_summary(dimensions)
    return {
        "session_id": session_id,
        "tier": session["tier"] if session else "UNKNOWN",
        "dimensions": dimensions,
        "summary": summary,
        "next_step": "Call draft_elicit to get targeted questions for MISSING/AMBIGUOUS fields.",
    }


@mcp.tool(annotations={"title": "Generate Elicitation Questions", **_RO})
def draft_elicit(session_id: str) -> dict:
    """Generate targeted elicitation questions for MISSING and AMBIGUOUS fields.

    Returns questions with suggested answer scaffolds.
    Present these to the human. Use draft_confirm to record their answers.

    Args:
        session_id: Active session ID.
    """
    questions = engine.generate_elicitation(session_id)
    return {
        "session_id": session_id,
        "question_count": len(questions),
        "questions": questions,
        "instruction": "Present these to the human. Record answers with draft_confirm.",
    }


@mcp.tool(annotations={"title": "Confirm DRAFT Field", **_WRITE})
def draft_confirm(session_id: str, field_key: str, value: str) -> dict:
    """Confirm a DRAFT field with a human-provided answer.

    Args:
        session_id: Active session ID.
        field_key: Field to confirm (e.g., "D1", "R3", "T2").
        value: The human's answer for this field.
    """
    return engine.confirm_field(session_id, field_key, value)


@mcp.tool(annotations={"title": "Surface Assumptions", **_RO})
def draft_assumptions(session_id: str) -> dict:
    """Surface 3-5 key assumptions as falsifiable claims.

    Present to human as: "I'm assuming X. Is that correct?"
    Use draft_verify to record their response.

    Args:
        session_id: Active session ID.
    """
    assumptions = engine.generate_assumptions(session_id)
    return {
        "session_id": session_id,
        "assumption_count": len(assumptions),
        "assumptions": [{"index": i, **a} for i, a in enumerate(assumptions)],
        "instruction": "Present each as a falsifiable claim. Use draft_verify to record human response.",
    }


@mcp.tool(annotations={"title": "Verify Assumption", **_WRITE})
def draft_verify(session_id: str, assumption_index: int, verified: bool, note: str = "") -> dict:
    """Verify or reject an assumption.

    If rejected, affected fields need re-elicitation.

    Args:
        session_id: Active session ID.
        assumption_index: Index of the assumption (from draft_assumptions).
        verified: True if human confirms, False if they reject.
        note: Optional human note.
    """
    return engine.verify_assumption(session_id, assumption_index, verified, note)


@mcp.tool(annotations={"title": "Check Confirmation Gate", **_RO})
def draft_gate(session_id: str) -> dict:
    """Check the confirmation gate: are all applicable fields confirmed?

    Returns GO (all clear) or NO-GO (with list of blockers).
    No execution should proceed until gate returns GO.

    Args:
        session_id: Active session ID.
    """
    return engine.check_gate(session_id)


@mcp.tool(annotations={"title": "Elicitation Quality Review", **_RO})
def draft_review(session_id: str) -> dict:
    """Elicitation quality self-assessment (Step 7).

    Mandatory for CONSEQUENTIAL tier. Recommended for STANDARD.
    Checks for perfunctory confirmations, uncaptured info, quality concerns.

    Args:
        session_id: Active session ID.
    """
    return engine.elicitation_review(session_id)


@mcp.tool(annotations={"title": "View Session State", **_RO})
def draft_status(session_id: str = "") -> dict:
    """View current DRAFT session state.

    Shows tier, dimension map, field statuses, assumptions, gate status.
    If no session_id provided, shows the active session.

    Args:
        session_id: Optional. Defaults to active session.
    """
    session = storage.get_active_session() if not session_id else storage.get_session(session_id)

    if not session:
        return {"error": "No active session. Use draft_intake to start one."}

    gate = engine.check_gate(session["id"])

    return {
        "session_id": session["id"],
        "tier": session["tier"],
        "intent": session.get("intent", "")[:200],
        "dimensions": _dimension_summary(session.get("dimensions", {})),
        "assumptions_count": len(session.get("assumptions", [])),
        "gate": gate["summary"],
        "review_done": bool(session.get("review_done")),
        "created_at": session.get("created_at"),
    }


@mcp.tool(annotations={"title": "Unscreen Dimension", **_WRITE})
def draft_unscreen(session_id: str, dimension_key: str) -> dict:
    """Reverse screening on a dimension that was incorrectly marked N/A.

    Only works on non-mandatory dimensions (R, A, F).
    Populates all fields as MISSING so they can be elicited and confirmed.

    Args:
        session_id: Active session ID.
        dimension_key: The dimension to unscreen ("R", "A", or "F").
    """
    return engine.unscreen_dimension(session_id, dimension_key)


@mcp.tool(annotations={"title": "Add Manual Assumption", **_CREATE})
def draft_add_assumption(session_id: str, claim: str, source: str = "manual", falsifier: str = "") -> dict:
    """Add a manually authored assumption to the session.

    Use for Devil's Advocate assumptions or any assumption not auto-generated
    by the screening/extraction system. Added assumptions integrate with
    draft_verify and draft_gate like auto-generated ones.

    Args:
        session_id: Active session ID.
        claim: The falsifiable claim.
        source: Origin of the assumption (default: "manual"). Use "devils_advocate" for DA step.
        falsifier: What would prove this wrong. Auto-generated if omitted.
    """
    return engine.add_assumption(session_id, claim, source, falsifier)


@mcp.tool(annotations={"title": "Override Blocked Gate", **_DESTRUCT})
def draft_override(session_id: str, reason: str) -> dict:
    """Override a blocked gate with a logged reason (authorized override).

    For tool limitations only — NOT a governance bypass. The override is
    audit-logged and distinguishable from normal PASS.

    Args:
        session_id: Active session ID.
        reason: Mandatory explanation of why override is justified.
    """
    return engine.override_gate(session_id, reason)


@mcp.tool(annotations={"title": "Close Session", **_DESTRUCT})
def draft_close(session_id: str) -> dict:
    """Close a DRAFT session.

    Args:
        session_id: Session to close.
    """
    storage.close_session(session_id)
    storage.log_audit(session_id, "draft_close", "session_closed", "")
    return {"session_id": session_id, "status": "closed"}


@mcp.tool(annotations={"title": "Escalate Tier", **_CREATE})
def draft_escalate(session_id: str, reason: str) -> dict:
    """Manually escalate session tier.

    Casual -> Standard -> Consequential. Cannot exceed Consequential.

    Args:
        session_id: Active session ID.
        reason: Why escalation is needed.
    """
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    tiers = ["CASUAL", "STANDARD", "CONSEQUENTIAL"]
    current = tiers.index(session["tier"]) if session["tier"] in tiers else 0
    if current >= 2:
        return {"tier": "CONSEQUENTIAL", "note": "Already at maximum tier."}

    new_tier = tiers[current + 1]
    storage.update_session(session_id, tier=new_tier)
    storage.log_audit(session_id, "draft_escalate", f"{session['tier']} -> {new_tier}", reason)
    return {"previous_tier": session["tier"], "new_tier": new_tier, "reason": reason}


@mcp.tool(annotations={"title": "De-escalate Tier", **_CREATE})
def draft_deescalate(session_id: str, reason: str) -> dict:
    """Manually de-escalate session tier (authorized override).

    Consequential -> Standard -> Casual. Logged but honored.

    Args:
        session_id: Active session ID.
        reason: Reason for de-escalation.
    """
    session = storage.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    tiers = ["CASUAL", "STANDARD", "CONSEQUENTIAL"]
    current = tiers.index(session["tier"]) if session["tier"] in tiers else 2
    if current <= 0:
        return {"tier": "CASUAL", "note": "Already at minimum tier."}

    new_tier = tiers[current - 1]
    storage.update_session(session_id, tier=new_tier)
    storage.log_audit(session_id, "draft_deescalate", f"{session['tier']} -> {new_tier}",
                      f"AUTHORIZED: {reason}")
    return {
        "previous_tier": session["tier"], "new_tier": new_tier, "reason": reason,
        "note": "De-escalation honored and logged. DRAFT mapping still occurs internally.",
    }


# ── Helpers ───────────────────────────────────────────────

def _next_step_for_tier(tier: str) -> str:
    if tier == "CASUAL":
        return "Casual tier — respond naturally. Internal DRAFT mapping only."
    elif tier == "STANDARD":
        return "Call draft_map with the user's full context to map DRAFT dimensions."
    else:
        return ("CONSEQUENTIAL: Call draft_map with full context. All 7 steps mandatory. "
                "Devil's Advocate in assumptions. Review required.")


def _dimension_summary(dimensions: dict) -> dict:
    """Summarize dimension statuses for display."""
    summary = {}
    for dim_key in ["D", "R", "A", "F", "T"]:
        fields = dimensions.get(dim_key, {})
        if isinstance(fields, dict) and fields.get("_screened"):
            summary[f"{dim_key} ({DIMENSION_NAMES.get(dim_key, '')})"] = "SCREENED (N/A)"
            continue
        statuses: dict[str, int] = {}
        for fk, info in fields.items():
            if fk.startswith("_"):
                continue
            s = info.get("status", "UNMAPPED")
            statuses[s] = statuses.get(s, 0) + 1
        summary[f"{dim_key} ({DIMENSION_NAMES.get(dim_key, '')})"] = statuses or "UNMAPPED"
    return summary
