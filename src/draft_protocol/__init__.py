"""DRAFT Protocol — Intake Governance for AI Tool Calls.

Ensures AI understands human intent before execution begins.

Usage:
    # As MCP server (primary use case):
    pip install draft-protocol
    python -m draft_protocol

    # As library:
    from draft_protocol.engine import classify_tier, map_dimensions, check_gate
    from draft_protocol.storage import create_session, get_session
    from draft_protocol.providers import llm_available, embed_available
"""

__version__ = "1.4.0"

# Public API — importable from `draft_protocol` directly
from draft_protocol.engine import (
    add_assumption,
    check_gate,
    classify_tier,
    confirm_batch,
    confirm_field,
    deescalate_tier,
    elicitation_review,
    escalate_tier,
    generate_assumptions,
    generate_elicitation,
    get_ceremony_depth,
    get_legacy_tier,
    map_dimensions,
    open_elicitation,
    override_gate,
    quick_confirm_satisfied,
    resolve_tier_override,
    score_assumptions,
    unscreen_dimension,
    verify_assumption,
    verify_batch,
)
from draft_protocol.extension_points import (
    clear_all_hooks,
    register_classify_hook,
    register_post_gate_hook,
    register_storage_path_hook,
)
from draft_protocol.providers import (
    embed_available,
    llm_available,
)
from draft_protocol.storage import (
    close_session,
    create_session,
    get_active_session,
    get_session,
)

__all__ = [
    "__version__",
    "add_assumption",
    "check_gate",
    # Engine
    "classify_tier",
    "clear_all_hooks",
    "close_session",
    "confirm_batch",
    "confirm_field",
    # Storage
    "create_session",
    "deescalate_tier",
    "elicitation_review",
    "embed_available",
    "escalate_tier",
    "generate_assumptions",
    "generate_elicitation",
    "get_active_session",
    "get_ceremony_depth",
    "get_legacy_tier",
    "get_session",
    # Providers
    "llm_available",
    "map_dimensions",
    "open_elicitation",
    "override_gate",
    "quick_confirm_satisfied",
    # Extension Points
    "register_classify_hook",
    "register_post_gate_hook",
    "register_storage_path_hook",
    "resolve_tier_override",
    "score_assumptions",
    "unscreen_dimension",
    "verify_assumption",
    "verify_batch",
]
