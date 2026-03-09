"""DRAFT Protocol Extension Points — Narrow Interface for Lab Overrides.

This module defines the ONLY functions that downstream consumers (like the
VectorLab draft_mcp wrapper) are permitted to override. Everything else in
draft_protocol is internal and may change between versions.

Extension Points (versioned contract):
  - classify_tier_hook: Override tier classification (e.g., GDE delegation)
  - post_gate_hook: Run after gate pass (e.g., cross-gate wiring)
  - storage_path_hook: Override DB location

Principle: OCTO-001 P3 (Narrow Bandwidth Interface)
  30,000 fibers, not full bandwidth. Override surface is minimal and explicit.

Version: 1.0 — Breaking changes require major version bump.
"""

from collections.abc import Callable

# ── Hook Registry ─────────────────────────────────────────
# Each hook is None by default (use built-in behavior).
# Set a hook to override the corresponding function.

_classify_tier_hook: Callable | None = None
_post_gate_hook: Callable | None = None
_storage_path_hook: Callable | None = None


def register_classify_hook(fn: Callable) -> None:
    """Register a custom tier classifier (e.g., GDE).

    fn signature: (message: str) -> tuple[str, str, float] | None
    Return (tier, reasoning, confidence) to override, or None to fall through.
    """
    global _classify_tier_hook
    _classify_tier_hook = fn


def register_post_gate_hook(fn: Callable) -> None:
    """Register a post-gate callback (e.g., cross-gate wiring).

    fn signature: (session_id: str, gate_result: dict) -> None
    """
    global _post_gate_hook
    _post_gate_hook = fn


def register_storage_path_hook(fn: Callable) -> None:
    """Register a custom storage path resolver.

    fn signature: () -> Path
    """
    global _storage_path_hook
    _storage_path_hook = fn


def get_classify_hook() -> Callable | None:
    return _classify_tier_hook


def get_post_gate_hook() -> Callable | None:
    return _post_gate_hook


def get_storage_path_hook() -> Callable | None:
    return _storage_path_hook


def clear_all_hooks() -> None:
    """Reset all hooks to None (useful for testing)."""
    global _classify_tier_hook, _post_gate_hook, _storage_path_hook
    _classify_tier_hook = None
    _post_gate_hook = None
    _storage_path_hook = None
