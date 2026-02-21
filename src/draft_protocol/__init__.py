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

__version__ = "0.1.0"

# Public API — importable from `draft_protocol` directly
from draft_protocol.engine import (
    add_assumption,
    check_gate,
    classify_tier,
    confirm_field,
    elicitation_review,
    generate_assumptions,
    generate_elicitation,
    map_dimensions,
    override_gate,
    unscreen_dimension,
    verify_assumption,
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
    # Engine
    "classify_tier",
    "map_dimensions",
    "generate_elicitation",
    "generate_assumptions",
    "check_gate",
    "confirm_field",
    "unscreen_dimension",
    "add_assumption",
    "override_gate",
    "verify_assumption",
    "elicitation_review",
    # Storage
    "create_session",
    "get_session",
    "get_active_session",
    "close_session",
    # Providers
    "llm_available",
    "embed_available",
]
