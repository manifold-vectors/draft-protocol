"""SQLite storage for DRAFT sessions."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from draft_protocol.config import DB_PATH

# M1.4: Valid tier enum — reject anything not in this set
VALID_TIERS = {"CASUAL", "STANDARD", "CONSEQUENTIAL"}


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            tier TEXT NOT NULL DEFAULT 'CASUAL',
            intent TEXT,
            provisional_interpretation TEXT,
            dimensions JSON NOT NULL DEFAULT '{}',
            assumptions JSON NOT NULL DEFAULT '[]',
            gate_passed INTEGER NOT NULL DEFAULT 0,
            review_done INTEGER NOT NULL DEFAULT 0,
            review_notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id),
            tool_name TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# Initialize on import
init_db()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(tier: str, intent: str) -> str:
    """Create a new DRAFT session. Returns session_id."""
    # M1.4: Validate tier enum
    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier '{tier}'. Must be one of: {', '.join(sorted(VALID_TIERS))}")
    sid = str(uuid.uuid4())[:12]
    conn = get_db()
    now = _now()
    conn.execute(
        "INSERT INTO sessions (id, tier, intent, dimensions, assumptions, created_at, updated_at) "
        "VALUES (?, ?, ?, '{}', '[]', ?, ?)",
        (sid, tier, intent, now, now),
    )
    conn.commit()
    conn.close()
    return sid


def get_session(session_id: str) -> dict | None:
    """Retrieve a session by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["dimensions"] = json.loads(d["dimensions"])
    d["assumptions"] = json.loads(d["assumptions"])
    return d


def is_session_closed(session_id: str) -> bool:
    """Check if a session is closed. M1.3: Closed session guard."""
    conn = get_db()
    row = conn.execute("SELECT closed_at FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return True  # Nonexistent sessions treated as closed
    return row["closed_at"] is not None


def get_active_session() -> dict | None:
    """Get the most recent unclosed session."""
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE closed_at IS NULL ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["dimensions"] = json.loads(d["dimensions"])
    d["assumptions"] = json.loads(d["assumptions"])
    return d


def update_session(session_id: str, **kwargs):
    """Update session fields. JSON fields auto-serialized."""
    # M1.4: Validate tier if being updated
    if "tier" in kwargs and kwargs["tier"] not in VALID_TIERS:
        raise ValueError(f"Invalid tier '{kwargs['tier']}'. Must be one of: {', '.join(sorted(VALID_TIERS))}")
    conn = get_db()
    sets = ["updated_at = ?"]
    vals = [_now()]
    for k, v in kwargs.items():
        if k in ("dimensions", "assumptions"):
            v = json.dumps(v)
        sets.append(f"{k} = ?")
        vals.append(v)
    vals.append(session_id)
    conn.execute(f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def close_session(session_id: str):
    """Mark session closed."""
    update_session(session_id, closed_at=_now())


def log_audit(session_id: str, tool_name: str, action: str, detail: str = ""):
    """Write audit trail entry."""
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (session_id, tool_name, action, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, tool_name, action, detail, _now()),
    )
    conn.commit()
    conn.close()
