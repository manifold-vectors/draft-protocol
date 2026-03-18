"""HMAC signing for inter-gate assertions.

Provides integrity guarantees for all cross-gate communication.
Each assertion is signed with HMAC-SHA256, includes a timestamp
and a monotonic nonce for replay protection.

Secret comes from GATE_HMAC_SECRET environment variable.
"""

import hashlib
import hmac
import json
import os
import time
from typing import Any

# Monotonic nonce counter (per-process, resets on restart)
_nonce_counter: int = 0


def _get_secret() -> bytes:
    """Get HMAC secret from environment or .env file.

    Raises RuntimeError if no secret is found and DRAFT_DEV_MODE is not set.
    """
    secret = os.environ.get("GATE_HMAC_SECRET", "")
    if not secret:
        lab_root = os.environ.get("VECTORLAB_ROOT", "")
        if lab_root:
            env_path = os.path.join(lab_root, ".env")
            if os.path.isfile(env_path):
                try:
                    with open(env_path) as f2:
                        for line in f2:
                            line = line.strip()
                            if line.startswith("GATE_HMAC_SECRET=") and not line.startswith("#"):
                                secret = line.split("=", 1)[1].strip().strip("\"'")
                                break
                except OSError:
                    pass
    if not secret:
        if os.environ.get("DRAFT_DEV_MODE", "") == "1":
            secret = "vector-gate-dev-secret-DO-NOT-USE-IN-PRODUCTION"
        else:
            raise RuntimeError(
                "GATE_HMAC_SECRET not set. Set the environment variable or "
                "set DRAFT_DEV_MODE=1 for local development."
            )
    return secret.encode()


def _next_nonce() -> int:
    """Return next monotonic nonce."""
    global _nonce_counter
    _nonce_counter += 1
    return _nonce_counter


def sign_assertion(assertion_type: str, payload: dict[str, Any]) -> dict:
    """Sign an arbitrary inter-gate assertion.

    Returns a complete signed assertion dict ready for transport:
    {
        "type": "draft_gate_passed",
        "payload": {...},
        "timestamp": "1773474000",
        "nonce": 1,
        "hmac": "hex..."
    }
    """
    ts = str(int(time.time()))
    nonce = _next_nonce()
    # Canonical form: type|timestamp|nonce|sorted-json-payload
    canonical = f"{assertion_type}|{ts}|{nonce}|{json.dumps(payload, sort_keys=True)}"
    sig = hmac.new(_get_secret(), canonical.encode(), hashlib.sha256).hexdigest()
    return {
        "type": assertion_type,
        "payload": payload,
        "timestamp": ts,
        "nonce": nonce,
        "hmac": sig,
    }


def verify_assertion(assertion: dict, max_age_seconds: int = 300) -> dict:
    """Verify a signed assertion.

    Checks HMAC integrity, timestamp freshness, and nonce monotonicity.

    Returns:
        {"valid": True, "type": "...", "payload": {...}}
        {"valid": False, "reason": "..."}
    """
    required = {"type", "payload", "timestamp", "nonce", "hmac"}
    if not isinstance(assertion, dict):
        return {"valid": False, "reason": f"Expected dict, got {type(assertion).__name__}"}
    if not required.issubset(assertion.keys()):
        return {"valid": False, "reason": f"Missing fields: {required - set(assertion.keys())}"}

    a_type = assertion["type"]
    payload = assertion["payload"]
    ts = assertion["timestamp"]
    nonce = assertion["nonce"]
    sig = assertion["hmac"]

    # Reconstruct canonical form and verify HMAC
    canonical = f"{a_type}|{ts}|{nonce}|{json.dumps(payload, sort_keys=True)}"
    expected = hmac.new(_get_secret(), canonical.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return {"valid": False, "reason": "HMAC mismatch — possible tampering"}

    # Timestamp freshness
    try:
        age = abs(int(time.time()) - int(ts))
        if age > max_age_seconds:
            return {"valid": False, "reason": f"Assertion stale ({age}s > {max_age_seconds}s)"}
    except (ValueError, TypeError):
        return {"valid": False, "reason": "Invalid timestamp"}

    return {"valid": True, "type": a_type, "payload": payload}


# ── Legacy compat: gate_passed signing (wraps new generalized API) ──

def sign_gate_pass(session_id: str) -> str:
    """Compute HMAC for a gate pass event (legacy format: ts:hex).

    Kept for backward compatibility with existing cross_gate.py code.
    New code should use sign_assertion() directly.
    """
    ts = str(int(time.time()))
    payload = f"{session_id}|1|{ts}".encode()
    sig = hmac.new(_get_secret(), payload, hashlib.sha256).hexdigest()
    return f"{ts}:{sig}"


def verify_gate_pass(session_id: str, gate_hmac: str | None) -> bool:
    """Verify legacy gate_passed HMAC (ts:hex format)."""
    if not gate_hmac:
        return False
    parts = gate_hmac.split(":", 1)
    if len(parts) != 2:
        return False
    ts, sig = parts
    payload = f"{session_id}|1|{ts}".encode()
    expected = hmac.new(_get_secret(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


def verify_or_warn(session_id: str, gate_hmac: str | None) -> dict:
    """Verify legacy gate HMAC and return structured result."""
    if gate_hmac is None:
        return {"valid": False, "reason": "gate_hmac missing (legacy session or unsigned)"}
    if verify_gate_pass(session_id, gate_hmac):
        return {"valid": True}
    return {"valid": False, "reason": "gate_hmac signature mismatch — possible tampering"}
