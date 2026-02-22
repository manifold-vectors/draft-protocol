"""Example: Using DRAFT Protocol as a Python library.

No server needed — import directly and use the engine.
"""
import os
import tempfile

# Use a temporary database for this example
os.environ["DRAFT_DB_PATH"] = tempfile.mktemp(suffix=".db")

from draft_protocol import (
    check_gate,
    classify_tier,
    close_session,
    confirm_field,
    create_session,
    generate_assumptions,
    generate_elicitation,
    get_session,
    map_dimensions,
)


def main():
    # ── Step 1: Classify the message ──────────────────────
    message = "Build a Python CLI that backs up my PostgreSQL database to S3"
    tier, reasoning, confidence = classify_tier(message)
    print(f"Tier: {tier} (confidence: {confidence:.2f})")
    print(f"Reasoning: {reasoning}\n")

    # ── Step 2: Create a session ──────────────────────────
    session_id = create_session(tier, message)
    print(f"Session: {session_id}\n")

    # ── Step 3: Map dimensions ────────────────────────────
    context = (
        "Build a Python CLI tool that backs up PostgreSQL databases to AWS S3. "
        "Uses pg_dump for extraction. Supports full and incremental backups. "
        "The tool must never drop or modify database tables. "
        "The founder is the decision maker. "
        "Success means a verified backup file exists in S3 with correct checksum."
    )
    dimensions = map_dimensions(session_id, context)

    print("Dimension mapping:")
    for dim_key, fields in dimensions.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            print(f"  {dim_key}: SCREENED (N/A)")
            continue
        for field_key, info in fields.items():
            if field_key.startswith("_"):
                continue
            status = info.get("status", "?")
            conf = info.get("confidence", 0)
            print(f"  {field_key}: {status} ({conf:.2f})")
    print()

    # ── Step 4: Ask about gaps ────────────────────────────
    questions = generate_elicitation(session_id)
    if questions:
        print(f"Questions for {len(questions)} gaps:")
        for q in questions[:3]:  # Show first 3
            print(f"  [{q['field']}] {q['question']}")
            if q.get("suggestion"):
                print(f"    Suggestion: {q['suggestion']}")
        print()

    # ── Step 5: Confirm fields ────────────────────────────
    # In real use, these come from the human. Here we simulate.
    session = get_session(session_id)
    dims = session["dimensions"]
    for dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for field_key in fields:
            if field_key.startswith("_"):
                continue
            confirm_field(session_id, field_key, f"Confirmed answer for {field_key}")

    # ── Step 6: Surface assumptions ───────────────────────
    assumptions = generate_assumptions(session_id)
    print(f"Assumptions ({len(assumptions)}):")
    for a in assumptions[:3]:
        print(f"  - {a['claim']}")
    print()

    # ── Step 7: Check gate ────────────────────────────────
    gate = check_gate(session_id)
    print(f"Gate: {gate['summary']}")
    if gate["passed"]:
        print("✅ All fields confirmed — execution authorized.")
    else:
        print(f"❌ Blocked: {gate['blockers']}")

    # ── Cleanup ───────────────────────────────────────────
    close_session(session_id)
    print(f"\nSession {session_id} closed.")


if __name__ == "__main__":
    main()
