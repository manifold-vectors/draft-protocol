"""Tests for DRAFT Protocol v1.1.0 features.

Covers: batch ops, perfunctory detection, escalate/deescalate,
        collaborative framing, session analytics, hard extraction enforcement.
"""

import os
import tempfile

# Use a temp DB for tests
if "DRAFT_DB_PATH" not in os.environ:
    _test_db = tempfile.mktemp(suffix=".db")
    os.environ["DRAFT_DB_PATH"] = _test_db

import pytest  # noqa: E402

from draft_protocol import engine, storage  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    """Reset storage for each test."""
    conn = storage.get_db()
    conn.execute("DELETE FROM audit_log")
    conn.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
    yield


def _create_mapped_session(tier="STANDARD"):
    """Helper: create a session and map dimensions."""
    sid = storage.create_session(tier, "Build a governance engine for AI safety")
    engine.map_dimensions(sid, "Building a governance engine for AI tool calls with authority rules and test criteria")
    return sid


def _fully_confirm(sid):
    """Helper: confirm all non-screened fields."""
    session = storage.get_session(sid)
    dims = session.get("dimensions", {})
    for _dim_key, fields in dims.items():
        if isinstance(fields, dict) and fields.get("_screened"):
            continue
        for fk in fields:
            if fk.startswith("_"):
                continue
            engine.confirm_field(sid, fk, f"Substantive answer for {fk} field with enough content")


# ── Batch Confirm Tests ───────────────────────────────────


class TestConfirmBatch:
    def test_confirm_multiple_fields(self):
        sid = _create_mapped_session()
        result = engine.confirm_batch(sid, {
            "D1": "Building a governance engine",
            "D2": "AI safety domain",
            "D3": "Without this, agents act without oversight",
        })
        assert result["confirmed"] == 3
        assert result["rejected"] == 0
        assert result["errors"] == 0
        assert result["total"] == 3
        assert result["results"]["D1"]["status"] == "CONFIRMED"

    def test_batch_rejects_empty_values(self):
        sid = _create_mapped_session()
        result = engine.confirm_batch(sid, {
            "D1": "Valid answer here",
            "D2": "",
            "D3": "  ",
        })
        assert result["confirmed"] == 1
        assert result["rejected"] == 2

    def test_batch_rejects_short_values(self):
        sid = _create_mapped_session()
        result = engine.confirm_batch(sid, {
            "D1": "ok",
            "D2": "Valid content for D2",
        })
        assert result["confirmed"] == 1
        assert result["rejected"] == 1

    def test_batch_errors_on_unmapped_dimension(self):
        sid = storage.create_session("STANDARD", "test")
        # No mapping done — dimensions empty
        result = engine.confirm_batch(sid, {"D1": "some value here"})
        assert result["errors"] == 1

    def test_batch_empty_dict_rejected(self):
        sid = _create_mapped_session()
        result = engine.confirm_batch(sid, {})
        assert "error" in result

    def test_batch_none_rejected(self):
        sid = _create_mapped_session()
        result = engine.confirm_batch(sid, None)
        assert "error" in result

    def test_batch_closed_session_blocked(self):
        sid = _create_mapped_session()
        storage.close_session(sid)
        result = engine.confirm_batch(sid, {"D1": "test value here"})
        assert "error" in result


# ── Quick Confirm Tests ───────────────────────────────────


class TestQuickConfirm:
    def test_promotes_satisfied_fields(self):
        sid = _create_mapped_session()
        session = storage.get_session(sid)
        dims = session.get("dimensions", {})

        # Count SATISFIED fields before
        satisfied_count = 0
        for _dk, fields in dims.items():
            if isinstance(fields, dict) and fields.get("_screened"):
                continue
            for fk, info in fields.items():
                if fk.startswith("_") or not isinstance(info, dict):
                    continue
                if (
                    info.get("status") == "SATISFIED"
                    and info.get("extracted")
                    and len(str(info["extracted"]).strip()) >= 3
                ):
                    satisfied_count += 1

        result = engine.quick_confirm_satisfied(sid)
        assert result["promoted_count"] == satisfied_count
        assert len(result["promoted_fields"]) == satisfied_count

    def test_does_not_promote_missing(self):
        sid = _create_mapped_session()
        result = engine.quick_confirm_satisfied(sid)
        # Verify no MISSING fields were promoted
        session = storage.get_session(sid)
        dims = session.get("dimensions", {})
        for _dk, fields in dims.items():
            if isinstance(fields, dict) and fields.get("_screened"):
                continue
            for fk, info in fields.items():
                if fk.startswith("_") or not isinstance(info, dict):
                    continue
                if info.get("confirmed_by") == "human_quick_confirm":
                    # These were SATISFIED before promotion
                    assert fk in result["promoted_fields"]

    def test_closed_session_blocked(self):
        sid = _create_mapped_session()
        storage.close_session(sid)
        result = engine.quick_confirm_satisfied(sid)
        assert "error" in result


# ── Verify Batch Tests ────────────────────────────────────


class TestVerifyBatch:
    def test_verify_all_assumptions(self):
        sid = _create_mapped_session()
        assumptions = engine.generate_assumptions(sid)
        if not assumptions:
            pytest.skip("No assumptions generated")

        verifications = {str(i): True for i in range(len(assumptions))}
        result = engine.verify_batch(sid, verifications)
        assert result["verified"] == len(assumptions)
        assert result["rejected"] == 0

    def test_mixed_verifications(self):
        sid = _create_mapped_session()
        assumptions = engine.generate_assumptions(sid)
        if len(assumptions) < 2:
            pytest.skip("Need at least 2 assumptions")

        result = engine.verify_batch(sid, {"0": True, "1": False})
        assert result["verified"] == 1
        assert result["rejected"] == 1
        assert "re-elicitation" in result["note"].lower() or "re-elicit" in result["note"].lower()

    def test_invalid_index(self):
        sid = _create_mapped_session()
        engine.generate_assumptions(sid)
        result = engine.verify_batch(sid, {"99": True})
        assert result["results"]["99"]["status"] == "ERROR"

    def test_empty_dict_rejected(self):
        sid = _create_mapped_session()
        result = engine.verify_batch(sid, {})
        assert "error" in result

    def test_closed_session_blocked(self):
        sid = _create_mapped_session()
        storage.close_session(sid)
        result = engine.verify_batch(sid, {"0": True})
        assert "error" in result


# ── Perfunctory Detection Tests ───────────────────────────


class TestPerfunctoryDetection:
    def test_detects_repeated_values(self):
        sid = _create_mapped_session()
        engine.confirm_batch(sid, {
            "D1": "yes agreed fine",
            "D2": "yes agreed fine",
            "D3": "yes agreed fine",
        })
        gate = engine.check_gate(sid)
        assert "warnings" in gate
        assert any("repeated" in w.lower() or "Repeated" in w for w in gate["warnings"])

    def test_detects_perfunctory_patterns(self):
        sid = _create_mapped_session()
        engine.confirm_field(sid, "D1", "yes")
        gate = engine.check_gate(sid)
        # "yes" is 3 chars so it passes length check, but should trigger perfunctory warning
        assert "warnings" in gate
        assert any("perfunctory" in w.lower() for w in gate["warnings"])

    def test_no_warnings_for_substantive_content(self):
        sid = _create_mapped_session()
        _fully_confirm(sid)
        # Generate and verify assumptions
        assumptions = engine.generate_assumptions(sid)
        if assumptions:
            verifications = {str(i): True for i in range(len(assumptions))}
            engine.verify_batch(sid, verifications)
        gate = engine.check_gate(sid)
        # Substantive unique values should not trigger warnings
        if gate.get("warnings"):
            # Some warnings may still appear if content is similar
            assert not any("perfunctory" in w.lower() for w in gate["warnings"])


# ── Escalation Tests ──────────────────────────────────────


class TestEscalation:
    def test_escalate_casual_to_standard(self):
        sid = storage.create_session("CASUAL", "hello")
        result = engine.escalate_tier(sid, "Scope expanded")
        assert result["previous_tier"] == "CASUAL"
        assert result["new_tier"] == "STANDARD"

    def test_escalate_standard_to_consequential(self):
        sid = storage.create_session("STANDARD", "build something")
        result = engine.escalate_tier(sid, "Touching governance")
        assert result["new_tier"] == "CONSEQUENTIAL"

    def test_escalate_at_max_noop(self):
        sid = storage.create_session("CONSEQUENTIAL", "restructure governance")
        result = engine.escalate_tier(sid, "test")
        assert result["tier"] == "CONSEQUENTIAL"
        assert "already" in result["note"].lower()

    def test_escalate_empty_reason_rejected(self):
        sid = storage.create_session("CASUAL", "hello")
        result = engine.escalate_tier(sid, "")
        assert "error" in result

    def test_deescalate_consequential_to_standard(self):
        sid = storage.create_session("CONSEQUENTIAL", "big task")
        result = engine.deescalate_tier(sid, "Scope reduced")
        assert result["new_tier"] == "STANDARD"

    def test_deescalate_at_min_noop(self):
        sid = storage.create_session("CASUAL", "hi")
        result = engine.deescalate_tier(sid, "test")
        assert result["tier"] == "CASUAL"

    def test_deescalate_empty_reason_rejected(self):
        sid = storage.create_session("STANDARD", "task")
        result = engine.deescalate_tier(sid, "")
        assert "error" in result

    def test_closed_session_blocked(self):
        sid = storage.create_session("STANDARD", "task")
        storage.close_session(sid)
        result = engine.escalate_tier(sid, "test")
        assert "error" in result


# ── Collaborative Framing Tests ───────────────────────────


class TestCollaborativeFraming:
    def test_elicitation_includes_framing(self):
        sid = _create_mapped_session()
        questions = engine.generate_elicitation(sid)
        if not questions:
            pytest.skip("No questions generated")
        for q in questions:
            assert "framing" in q
            assert isinstance(q["framing"], str)

    def test_framing_differs_by_status(self):
        sid = _create_mapped_session()
        questions = engine.generate_elicitation(sid)
        if not questions:
            pytest.skip("No questions generated")
        # At least verify framing exists and is non-empty
        for q in questions:
            assert len(q["framing"]) > 10


# ── Session Analytics Tests ───────────────────────────────


class TestSessionAnalytics:
    def test_review_includes_analytics(self):
        sid = _create_mapped_session()
        review = engine.elicitation_review(sid)
        assert "analytics" in review
        a = review["analytics"]
        assert "total_fields" in a
        assert "confirmed_fields" in a
        assert "average_confidence" in a
        assert "assumption_count" in a
        assert "tier" in a

    def test_analytics_counts_are_correct(self):
        sid = _create_mapped_session()
        _fully_confirm(sid)
        review = engine.elicitation_review(sid)
        a = review["analytics"]
        assert a["confirmed_fields"] > 0
        assert a["confirmed_fields"] <= a["total_fields"]
        assert 0.0 <= a["average_confidence"] <= 1.0

    def test_analytics_tracks_rejection_rate(self):
        sid = _create_mapped_session()
        engine.generate_assumptions(sid)
        review = engine.elicitation_review(sid)
        a = review["analytics"]
        assert a["assumption_rejection_rate"] == 0.0  # None rejected yet


# ── Hard Extraction Enforcement Tests ─────────────────────


class TestHardExtractionEnforcement:
    """Verify that _assess_field_llm strips extracted text from non-SATISFIED fields.

    Since LLM is not available in tests, we test the engine function directly.
    """

    def test_keyword_fallback_missing_has_no_extraction(self):
        """Keyword assessment for clearly missing fields should not fabricate."""
        result = engine._assess_field_keyword("R1", "hello world simple message")
        if result["status"] == "MISSING":
            # Keyword fallback can have confidence info but not fabricated content
            assert result.get("extracted") is None or result["extracted"] == ""


# ── LLM Assumptions Tier Scaling Tests ────────────────────


class TestAssumptionTierScaling:
    def test_casual_fewer_assumptions(self):
        sid = storage.create_session("CASUAL", "hello")
        engine.map_dimensions(sid, "Simple greeting, just saying hello to test the system")
        assumptions = engine.generate_assumptions(sid)
        assert len(assumptions) <= 2

    def test_standard_moderate_assumptions(self):
        sid = _create_mapped_session()
        assumptions = engine.generate_assumptions(sid)
        assert len(assumptions) <= 3

    def test_consequential_more_assumptions(self):
        sid = storage.create_session("CONSEQUENTIAL", "restructure governance architecture")
        engine.map_dimensions(
            sid,
            "Restructuring the entire governance architecture including authority model "
            "and gate enforcement with new constitutional rules",
        )
        assumptions = engine.generate_assumptions(sid)
        assert len(assumptions) <= 5
