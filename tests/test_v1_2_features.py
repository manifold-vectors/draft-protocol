"""Tests for DRAFT Protocol v1.2.0 features.

Covers: 5-tier classification, open elicitation, assumption quality scoring,
        ceremony depth, legacy tier compatibility.
"""

import os
import tempfile

if "DRAFT_DB_PATH" not in os.environ:
    _test_db = tempfile.mktemp(suffix=".db")
    os.environ["DRAFT_DB_PATH"] = _test_db

import pytest  # noqa: E402

from draft_protocol import engine, storage  # noqa: E402
from draft_protocol.config import (  # noqa: E402
    ALL_TIERS,
    LEGACY_MAP,
    TIER_ASSUMPTIONS,
    TIER_CEREMONY,
    TIER_TO_LEGACY,
)


@pytest.fixture(autouse=True)
def _fresh_db():
    """Reset storage for each test."""
    conn = storage.get_db()
    conn.execute("DELETE FROM audit_log")
    conn.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
    yield


def _create_mapped_session(tier="TASK"):
    """Helper: create a session and map dimensions."""
    sid = storage.create_session(tier, "Build a governance engine for AI safety")
    engine.map_dimensions(
        sid,
        "Building a governance engine for AI tool calls with authority rules and test criteria",
    )
    return sid


# ── 5-Tier Classification Tests ──────────────────────────


class TestFiveTierClassification:
    def test_trivial_greeting(self):
        tier, _, _ = engine.classify_tier("hello")
        assert tier == "TRIVIAL"

    def test_trivial_acknowledgment(self):
        tier, _, _ = engine.classify_tier("yes")
        assert tier == "TRIVIAL"

    def test_trivial_continue(self):
        tier, _, _ = engine.classify_tier("continue")
        assert tier == "TRIVIAL"

    def test_trivial_short_no_action(self):
        tier, _, _ = engine.classify_tier("ok done")
        assert tier == "TRIVIAL"

    def test_lookup_question(self):
        tier, _, _ = engine.classify_tier("what is the status of the deployment")
        assert tier in ("LOOKUP", "TASK")  # "status" is LOOKUP, but "deployment" could push to TASK

    def test_lookup_check(self):
        tier, _, _ = engine.classify_tier("check the logs")
        assert tier in ("LOOKUP", "TASK")

    def test_task_build(self):
        tier, _, _ = engine.classify_tier("build a Python script to parse CSV files")
        assert tier == "TASK"

    def test_task_implement(self):
        tier, _, _ = engine.classify_tier("implement a caching layer for the API")
        assert tier == "TASK"

    def test_multi_docker(self):
        tier, _, _ = engine.classify_tier("update docker-compose and restart services")
        assert tier == "MULTI"

    def test_multi_migrate(self):
        tier, _, _ = engine.classify_tier("migrate the database schema across all services")
        assert tier == "MULTI"

    def test_multi_pattern(self):
        tier, _, _ = engine.classify_tier("update 5 files across multiple services")
        assert tier == "MULTI"

    def test_consequential_governance(self):
        tier, _, _ = engine.classify_tier("restructure the governance architecture")
        assert tier == "CONSEQUENTIAL"

    def test_consequential_authority(self):
        tier, _, _ = engine.classify_tier("change the authority model for deployments")
        assert tier == "CONSEQUENTIAL"

    def test_empty_rejected(self):
        tier, _, _ = engine.classify_tier("")
        assert tier == "REJECTED"

    def test_none_rejected(self):
        tier, _, _ = engine.classify_tier(None)
        assert tier == "REJECTED"

    def test_all_tiers_in_config(self):
        assert len(ALL_TIERS) == 5
        assert "TRIVIAL" in ALL_TIERS
        assert "CONSEQUENTIAL" in ALL_TIERS


# ── Legacy Compatibility Tests ────────────────────────────


class TestLegacyCompat:
    def test_legacy_map_exists(self):
        assert LEGACY_MAP["CASUAL"] == "TRIVIAL"
        assert LEGACY_MAP["STANDARD"] == "TASK"
        assert LEGACY_MAP["CONSEQUENTIAL"] == "CONSEQUENTIAL"

    def test_reverse_map(self):
        assert TIER_TO_LEGACY["TRIVIAL"] == "CASUAL"
        assert TIER_TO_LEGACY["LOOKUP"] == "CASUAL"
        assert TIER_TO_LEGACY["TASK"] == "STANDARD"
        assert TIER_TO_LEGACY["MULTI"] == "STANDARD"
        assert TIER_TO_LEGACY["CONSEQUENTIAL"] == "CONSEQUENTIAL"

    def test_resolve_legacy_override(self):
        assert engine.resolve_tier_override("CASUAL") == "TRIVIAL"
        assert engine.resolve_tier_override("STANDARD") == "TASK"
        assert engine.resolve_tier_override("CONSEQUENTIAL") == "CONSEQUENTIAL"

    def test_resolve_new_override(self):
        assert engine.resolve_tier_override("TRIVIAL") == "TRIVIAL"
        assert engine.resolve_tier_override("MULTI") == "MULTI"

    def test_resolve_invalid_override(self):
        assert engine.resolve_tier_override("INVALID") == ""

    def test_get_legacy_tier(self):
        assert engine.get_legacy_tier("TRIVIAL") == "CASUAL"
        assert engine.get_legacy_tier("TASK") == "STANDARD"

    def test_create_session_with_legacy_tier(self):
        # CASUAL is accepted but maps to TRIVIAL internally
        sid = storage.create_session("CASUAL", "hello")
        session = storage.get_session(sid)
        assert session["tier"] == "TRIVIAL"  # Legacy CASUAL → TRIVIAL

    def test_create_session_with_new_tier(self):
        sid = storage.create_session("MULTI", "migrate databases")
        session = storage.get_session(sid)
        assert session["tier"] == "MULTI"


# ── Ceremony Depth Tests ─────────────────────────────────


class TestCeremonyDepth:
    def test_trivial_invisible(self):
        assert TIER_CEREMONY["TRIVIAL"] == "invisible"

    def test_lookup_tag(self):
        assert TIER_CEREMONY["LOOKUP"] == "tag"

    def test_task_semi_visible(self):
        assert TIER_CEREMONY["TASK"] == "semi_visible"

    def test_multi_visible(self):
        assert TIER_CEREMONY["MULTI"] == "visible"

    def test_consequential_full(self):
        assert TIER_CEREMONY["CONSEQUENTIAL"] == "full"

    def test_get_ceremony_depth(self):
        assert engine.get_ceremony_depth("TRIVIAL") == "invisible"
        assert engine.get_ceremony_depth("CONSEQUENTIAL") == "full"


# ── Open Elicitation Tests ────────────────────────────────


class TestOpenElicitation:
    def test_trivial_skipped(self):
        sid = storage.create_session("TRIVIAL", "hello")
        result = engine.open_elicitation(sid)
        assert result["skipped"] is True

    def test_lookup_skipped(self):
        sid = storage.create_session("LOOKUP", "check status")
        result = engine.open_elicitation(sid)
        assert result["skipped"] is True

    def test_task_generates_question(self):
        sid = storage.create_session("TASK", "build a REST API")
        result = engine.open_elicitation(sid)
        assert "question" in result
        assert len(result["question"]) > 10

    def test_multi_generates_question(self):
        sid = storage.create_session("MULTI", "migrate all databases")
        result = engine.open_elicitation(sid)
        assert "question" in result

    def test_consequential_generates_question(self):
        sid = storage.create_session("CONSEQUENTIAL", "restructure governance")
        result = engine.open_elicitation(sid)
        assert "question" in result
        assert "framing" in result

    def test_closed_session_blocked(self):
        sid = storage.create_session("TASK", "test")
        storage.close_session(sid)
        result = engine.open_elicitation(sid)
        assert "error" in result


# ── Assumption Quality Scoring Tests ──────────────────────


class TestAssumptionQualityScoring:
    def test_score_returns_results(self):
        sid = _create_mapped_session()
        engine.generate_assumptions(sid)
        result = engine.score_assumptions(sid)
        assert result["scored"] > 0
        assert "results" in result
        assert "average_quality" in result

    def test_score_has_three_dimensions(self):
        sid = _create_mapped_session()
        engine.generate_assumptions(sid)
        result = engine.score_assumptions(sid)
        for r in result["results"]:
            assert "falsifiability" in r
            assert "impact" in r
            assert "novelty" in r
            assert "quality_score" in r
            assert 0.0 <= r["quality_score"] <= 1.0

    def test_low_quality_flagged(self):
        sid = _create_mapped_session()
        engine.generate_assumptions(sid)
        result = engine.score_assumptions(sid)
        # At least check the flag mechanism works
        for r in result["results"]:
            if r["quality_score"] < 0.4:
                assert r["low_quality"] is True

    def test_no_assumptions_handled(self):
        sid = storage.create_session("TASK", "test")
        result = engine.score_assumptions(sid)
        assert result["scored"] == 0

    def test_closed_session_blocked(self):
        sid = _create_mapped_session()
        storage.close_session(sid)
        result = engine.score_assumptions(sid)
        assert "error" in result

    def test_quality_stored_in_session(self):
        sid = _create_mapped_session()
        engine.generate_assumptions(sid)
        engine.score_assumptions(sid)
        session = storage.get_session(sid)
        assumptions = session.get("assumptions", [])
        if assumptions:
            assert "quality_score" in assumptions[0]


# ── 5-Tier Escalation Tests ──────────────────────────────


class TestFiveTierEscalation:
    def test_escalate_trivial_to_lookup(self):
        sid = storage.create_session("TRIVIAL", "hi")
        result = engine.escalate_tier(sid, "Needs more info")
        assert result["new_tier"] == "LOOKUP"

    def test_escalate_lookup_to_task(self):
        sid = storage.create_session("LOOKUP", "check something")
        result = engine.escalate_tier(sid, "Needs work")
        assert result["new_tier"] == "TASK"

    def test_escalate_task_to_multi(self):
        sid = storage.create_session("TASK", "build X")
        result = engine.escalate_tier(sid, "Cross-service")
        assert result["new_tier"] == "MULTI"

    def test_escalate_multi_to_consequential(self):
        sid = storage.create_session("MULTI", "migrate")
        result = engine.escalate_tier(sid, "Touches governance")
        assert result["new_tier"] == "CONSEQUENTIAL"

    def test_escalate_at_max(self):
        sid = storage.create_session("CONSEQUENTIAL", "governance")
        result = engine.escalate_tier(sid, "test")
        assert "already" in result.get("note", "").lower() or result.get("tier") == "CONSEQUENTIAL"

    def test_deescalate_consequential_to_multi(self):
        sid = storage.create_session("CONSEQUENTIAL", "big task")
        result = engine.deescalate_tier(sid, "Scope reduced")
        assert result["new_tier"] == "MULTI"

    def test_deescalate_at_min(self):
        sid = storage.create_session("TRIVIAL", "hi")
        result = engine.deescalate_tier(sid, "test")
        assert result.get("tier") == "TRIVIAL" or "already" in result.get("note", "").lower()


# ── Tier Assumption Count Tests ───────────────────────────


class TestTierAssumptionCounts:
    def test_trivial_zero_assumptions(self):
        assert TIER_ASSUMPTIONS["TRIVIAL"] == 0

    def test_lookup_one_assumption(self):
        assert TIER_ASSUMPTIONS["LOOKUP"] == 1

    def test_task_two_assumptions(self):
        assert TIER_ASSUMPTIONS["TASK"] == 2

    def test_multi_three_assumptions(self):
        assert TIER_ASSUMPTIONS["MULTI"] == 3

    def test_consequential_five_assumptions(self):
        assert TIER_ASSUMPTIONS["CONSEQUENTIAL"] == 5

    def test_trivial_generates_zero(self):
        sid = storage.create_session("TRIVIAL", "hi")
        engine.map_dimensions(sid, "Just saying hello")
        assumptions = engine.generate_assumptions(sid)
        assert len(assumptions) == 0

    def test_task_generates_up_to_two(self):
        sid = _create_mapped_session("TASK")
        assumptions = engine.generate_assumptions(sid)
        assert len(assumptions) <= 2

    def test_consequential_generates_up_to_five(self):
        sid = storage.create_session("CONSEQUENTIAL", "restructure governance")
        engine.map_dimensions(
            sid,
            "Restructuring the entire governance architecture including authority model "
            "and gate enforcement with new constitutional rules",
        )
        assumptions = engine.generate_assumptions(sid)
        assert len(assumptions) <= 5
