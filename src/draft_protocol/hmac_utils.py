"""HMAC signing for gate_passed — prevents spoofing of gate status.

The gate_passed flag is the critical trust signal that threads through
the cross-gate pipeline. Without signing, any process with SQLite write
access could flip gate_passed=1 and bypass DRAFT governance.

HMAC-SHA256 signs: session_id | gate_passed | timestamp
Secret comes from GATE_HMAC_SECRET environment variable.
"""

import hashlib
import hmac
import os
import time


def _get_secret() -> bytes:
    """Get HMAC secret from environment. Falls back to a default for dev."""
    secret = os.environ.get("GATE_HMAC_SECRET", "")
    if not secret:
        # Dev fallback — NOT safe for production
        secret = "vector-gate-dev-secret-change-me"
    return secret.encode()


def sign_gate_pass(session_id: str) -> str:
    """Compute HMAC for a gate pass event.

    Returns hex-encoded HMAC string to store alongside gate_passed=1.
    The timestamp is embedded in the signature payload so the same
    session_id doesn't produce the same HMAC if re-signed.
    """
    ts = str(int(time.time()))
    payload = f"{session_id}|1|{ts}".encode()
    sig = hmac.new(_get_secret(), payload, hashlib.sha256).hexdigest()
    # Return ts:sig so verifier can reconstruct the payload
    return f"{ts}:{sig}"


def verify_gate_pass(session_id: str, gate_hmac: str | None) -> bool:
    """Verify that a gate_passed=1 was legitimately signed.

    Returns True if HMAC is valid, False if missing/invalid/tampered.
    """
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
    """Verify gate HMAC and return structured result for cross-gate use.

    Returns:
        {"valid": True} if HMAC checks out
        {"valid": False, "reason": "..."} if not
    """
    if gate_hmac is None:
        return {"valid": False, "reason": "gate_hmac missing (legacy session or unsigned)"}

    if verify_gate_pass(session_id, gate_hmac):
        return {"valid": True}

    return {"valid": False, "reason": "gate_hmac signature mismatch — possible tampering"}
